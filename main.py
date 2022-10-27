# ===========================================================================================================================================================
# Config part
CalUrl=""
BotToken=""
Timezone="Europe/Paris"
AdminId=""
# End of config part
# ===========================================================================================================================================================

# Code by Wiibleyde

import discord 
import os
import requests
import icalendar
import datetime
import pytz
import sys
import asyncio

client = discord.Client()

@client.event
async def on_ready():
    stderr("We have logged in as {0.user}".format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$next'):
        cal = parse_ical()
        event = getNextEvent(cal)
        timeleft = CalcTimeLeft(event)
        embed = discord.Embed(title="Prochain cours", description=getTitle(event.get('summary')), color=0x00ff00)
        if isMoreThanDay(timeleft):
            embed.add_field(name="Dans", value=str(timeleft.days) + " jours", inline=False)
            await message.channel.send(embed=embed)
        else:
            eventdate = getEventDate(event) + datetime.timedelta(hours=2)
            eventdate = eventdate.strftime("%d/%m %H:%M")
            embed.add_field(name="Dans " + str(getHours(timeleft)) + "h" + str(getMinutes(timeleft)) + "m", value=eventdate, inline=False)
            await message.channel.send(embed=embed)

    if message.content.startswith('$help'):
        embed = discord.Embed(title="Help", description="Liste des commandes" + "\n- $next : Get next event in the given calendar" + "\n- $week : Get event of the current week in the given calendar", color=0xeee657)
        await message.channel.send(embed=embed)

    if message.content.startswith('$update') and message.author.id == AdminId:
        delete_ical()
        download_ical()
        await message.channel.send("Calendar updated")
    
    if message.content.startswith('$week'):
        cal = parse_ical()
        WeekEvents = getEventsWeek(cal)
        embed = discord.Embed(title="Cours de la semaine", description="Liste des cours de la semaine", color=0x00ff00)
        for event in WeekEvents:
            timeleft = CalcTimeLeft(event)
            eventdate = getEventDate(event) + datetime.timedelta(hours=2)
            if eventdate.strftime("%H:%M") == "00:00":
                eventdate = eventdate.strftime("%d/%m")
            else:
                eventdate = eventdate.strftime("%d/%m %H:%M")
            embed.add_field(name=getTitle(event.get('summary')), value=eventdate, inline=False)
        await message.channel.send(embed=embed)

async def my_background_task():
    await client.wait_until_ready()
    count=0
    while not client.is_closed():
        if count == 30:
            delete_ical()
            download_ical()
            count=0
        else:
            count=count+1
            stderr("Waiting " + str(30-count) + " minutes")
        cal=parse_ical()
        event=getNextEvent(cal)
        timeleft=CalcTimeLeft(event)
        stderr("Next event in : " + str(timeleft) + " : " + event.get('summary') + " : " + getEventDate(event).strftime("%d/%m/%Y %H:%M:%S"))
        stderr("Reload status")
        if isMoreThanDay(timeleft):
            await client.change_presence(activity=discord.Game(name=getTitle(event.get('summary')) + " dans plus d'un jour"))
        else:
            await client.change_presence(activity=discord.Game(name=getTitle(event.get('summary')) + " dans " + str(getHours(timeleft)) + "h" + str(getMinutes(timeleft)) + "m"))
        await asyncio.sleep(60)

client.loop.create_task(my_background_task())

def download_ical():
    try:
        r = requests.get(CalUrl, allow_redirects=True)
        open('calendar.ics', 'wb').write(r.content)
    except:
        stderr("Error downloading calendar")
        sys.exit(1)

def parse_ical():
    try:
        cal = icalendar.Calendar.from_ical(open('calendar.ics', 'rb').read())
        return cal
    except:
        stderr("Error parsing calendar")
        sys.exit(1)

def getEventDate(event):
    if type(event.get('dtstart').dt) is datetime.date:
        return datetime.datetime.combine(event.get('dtstart').dt, datetime.time(0, 0, 0), tzinfo=pytz.timezone(Timezone))
    return event.get('dtstart').dt

def getNextEvent(cal):
    """Return the next event in the calendar

    Args:
        cal (icalendar.Calendar): The calendar

    Returns:
        icalendar.Event: The next event
    """
    events = getAllEvents(cal)
    sorted_events = sorted(events, key=lambda event: getEventDate(event))
    now=datetime.datetime.now(pytz.timezone(Timezone))
    for event in sorted_events:
        if getEventDate(event) > now:
            if getTitle(event.get('summary')) == "Férié":
                continue
            return event

def stderr(message):
    """Print a message to stderr
    
    Args:
        message (string): The message to print

    Returns:
        None
    """
    print(message)

def getAllEvents(cal):
    """Return all events in the calendar

    Args:
        cal (icalendar.Calendar): The calendar

    Returns:
        list: List of icalendar.Event
    """
    events = []
    for event in cal.walk('vevent'):
        events.append(event)
    return events

def CalcTimeLeft(event):
    """Return the time left before the event

    Args:
        event (icalendar.Event): The event

    Returns:
        datetime.timedelta: The time left
    """
    timeleft=getEventDate(event)-datetime.datetime.now(pytz.timezone(Timezone))
    if getHours(timeleft) < 0:
        return 0
    return timeleft

def delete_ical():
    """Delete the calendar file

    Returns:
        None
    """
    try:
        os.remove("calendar.ics")
    except:
        stderr("Error deleting calendar")

def getMinutes(timeleft):
    """Return the minutes left before the event
    
    Args:
        timeleft (datetime.timedelta): The time left

    Returns:
        int: The minutes left
    """
    return timeleft.seconds // 60 - getHours(timeleft) * 60

def getHours(timeleft):
    """Return the hours left before the event

    Args:
        timeleft (datetime.timedelta): The time left

    Returns:
        int: The hours left
    """
    return timeleft.seconds // 3600

def getTitle(event):
    """Return the title of the event

    Args:
        event (string): The event

    Returns:
        string: The title
    """
    return event.split(" - ")[0]

def isMoreThanDay(timeleft):
    """Return if the time left is more than a day

    Args:
        timeleft (datetime.timedelta): The time left

    Returns:
        bool: True if more than a day, False otherwise
    """
    return timeleft.days > 0

def InEvent(cal):
    """Return if the bot is in an event

    Args:
        cal (icalendar.Calendar): The calendar

    Returns:
        bool: True if in an event, False otherwise
    """
    for event in cal.walk('vevent'):
        if getEventDate(event) < datetime.datetime.now(pytz.timezone(Timezone)) and getEventDate(event) + datetime.timedelta(minutes=30) > datetime.datetime.now(pytz.timezone(Timezone)):
            return True
    return False

def getEventsWeek(cal):
    """Return the events of the week

    Args:
        cal (icalendar.Calendar): The calendar

    Returns:
        list: List of icalendar.Event
    """
    events = []
    sorted_events = sortEvents(cal)
    for event in sorted_events:
        print(getTitle(event.get('summary')))
        if getEventDate(event) > datetime.datetime.now(pytz.timezone(Timezone)) and getEventDate(event) < datetime.datetime.now(pytz.timezone(Timezone)) + datetime.timedelta(days=7):
            if getTitle(event.get('summary')) == "Férié":
                continue
            events.append(event)
    return events

def sortEvents(cal):
    """Return the events sorted by date

    Args:
        cal (icalendar.Calendar): The calendar

    Returns:
        list: List of icalendar.Event
    """    
    events = []
    for event in cal.walk('vevent'):
        events.append(event)
    return sorted(events, key=lambda event: getEventDate(event))

if __name__ == "__main__":
    delete_ical()
    download_ical()
    client.run(BotToken)