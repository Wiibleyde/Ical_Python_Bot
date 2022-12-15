# ===========================================================================================================================================================
# Config part
CalUrl=""
BotToken=""
Timezone=""
AdminName=""
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
import sqlite3
import time

client = discord.Client(intents=discord.Intents.all())

class Database():
    def __init__(self,fileName):
        self.fileName = fileName

    def CreateDB(self):
        conn = sqlite3.connect(self.fileName)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                        (date text, time text, user text, cmd text)''')
        conn.commit()
        conn.close()

    def AddLog(self,user,cmd):
        conn = sqlite3.connect(self.fileName)
        c = conn.cursor()
        c.execute("INSERT INTO logs VALUES (?,?,?,?)", (time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"), user, cmd))
        conn.commit()
        conn.close()

    def GetNbCmdUsed(self):
        conn = sqlite3.connect(self.fileName)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM logs")
        result = c.fetchone()
        conn.close()
        return result[0]

    def GetNbCmdUsedByUser(self,user):
        conn = sqlite3.connect(self.fileName)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM logs WHERE user=?", (user,))
        result = c.fetchone()
        conn.close()
        return result[0]

    def GetNbCmdUsedByCmd(self,cmd):
        conn = sqlite3.connect(self.fileName)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM logs WHERE cmd=?", (cmd,))
        result = c.fetchone()
        conn.close()
        return result[0]

    def GetNbCmdUsedByUserAndCmd(self,user,cmd):
        conn = sqlite3.connect(self.fileName)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM logs WHERE user=? AND cmd=?", (user,cmd))
        result = c.fetchone()
        conn.close()
        return result[0]

@client.event
async def on_ready():
    showerfunc("We have logged in as {0.user}".format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$next'):
        LogsObj.AddLog(message.author.name,"$next")
        cal = parse_ical()
        event = getNextEvent(cal)
        timeleft = CalcTimeLeft(event)
        embed = discord.Embed(title="Prochain cours", description=getTitle(event.get('summary')), color=0x00ff00)
        if isMoreThanDay(timeleft):
            embed.add_field(name="Dans", value=str(timeleft.days) + " jours", inline=False)
            await message.channel.send(embed=embed)
        else:
            eventdate = getEventDate(event)
            eventdate = (eventdate + datetime.timedelta(hours=1)).strftime("%d/%m %H:%M")
            embed.add_field(name="Dans " + str(getHours(timeleft)) + "h" + str(getMinutes(timeleft)) + "m", value=eventdate, inline=False)
            await message.channel.send(embed=embed)

    if message.content.startswith('$update') and message.author.name == AdminName:
        LogsObj.AddLog(message.author.name,"$update")
        delete_ical()
        download_ical()
        await message.channel.send("Calendar updated")
    
    if message.content.startswith('$week'):
        LogsObj.AddLog(message.author.name,"$week")
        cal = parse_ical()
        WeekEvents = getEventsWeek(cal)
        embed = discord.Embed(title="Cours de la semaine", description="Liste des cours de la semaine", color=0x00ff00)
        for event in WeekEvents:
            timeleft = CalcTimeLeft(event)
            eventdate = getEventDate(event)
            if eventdate.strftime("%H:%M") == "00:00":
                eventdate = eventdate.strftime("%d/%m")
            else:
                eventdate = (eventdate + datetime.timedelta(hours=1)).strftime("%d/%m %H:%M")
            embed.add_field(name=getTitle(event.get('summary')), value=eventdate, inline=False)
        await message.channel.send(embed=embed)

    if message.content.startswith('$wiibleyde'):
        LogsObj.AddLog(message.author.name,"$wiibleyde")
        await message.channel.send("https://media.discordapp.net/attachments/940562878971400193/1016713259971268659/CAT_DANCE.gif")

    if message.content.startswith('$stats'):
        LogsObj.AddLog(message.author.name,"$stats")
        embed = discord.Embed(title="Stats", description="Statistiques", color=0x00ff00)
        embed.add_field(name="Nombre de commandes", value=str(LogsObj.GetNbCmdUsed()), inline=False)
        embed.add_field(name="Nombre de commandes par " + message.author.name, value=str(LogsObj.GetNbCmdUsedByUser(message.author.name)), inline=False)
        await message.channel.send(embed=embed)
        
    if message.content.startswith('$cmdstats') and message.author.name == AdminName:
        LogsObj.AddLog(message.author.name,"$cmdstats")
        embed = discord.Embed(title="Stats", description="Statistiques", color=0x00ff00)
        embed.add_field(name="Nombre de commandes $next", value=str(LogsObj.GetNbCmdUsedByCmd("$next")), inline=False)
        embed.add_field(name="Nombre de commandes $week", value=str(LogsObj.GetNbCmdUsedByCmd("$week")), inline=False)
        embed.add_field(name="Nombre de commandes $help", value=str(LogsObj.GetNbCmdUsedByCmd("$help")), inline=False)
        embed.add_field(name="Nombre de commandes $update", value=str(LogsObj.GetNbCmdUsedByCmd("$update")), inline=False)
        embed.add_field(name="Nombre de commandes $stats", value=str(LogsObj.GetNbCmdUsedByCmd("$stats")), inline=False)
        embed.add_field(name="Nombre de commandes $statscmd", value=str(LogsObj.GetNbCmdUsedByCmd("$statscmd")), inline=False)
        embed.add_field(name="Nombre de commandes $wiibleyde", value=str(LogsObj.GetNbCmdUsedByCmd("$wiibleyde")), inline=False)
        await message.channel.send(embed=embed)

    if message.content.startswith('$cmdstatsbyuser') and message.author.name == AdminName:
        LogsObj.AddLog(message.author.name,"$cmdstatsbyuser")
        user=message.content.split(" ")[1]
        embed = discord.Embed(title="Stats", description="Statistiques", color=0x00ff00)
        embed.add_field(name="Nombre de commandes $next par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$next",user)), inline=False)
        embed.add_field(name="Nombre de commandes $week par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$week",user)), inline=False)
        embed.add_field(name="Nombre de commandes $help par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$help",user)), inline=False)
        embed.add_field(name="Nombre de commandes $update par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$update",user)), inline=False)
        embed.add_field(name="Nombre de commandes $stats par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$stats",user)), inline=False)
        embed.add_field(name="Nombre de commandes $statscmd par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$statscmd",user)), inline=False)
        embed.add_field(name="Nombre de commandes $wiibleyde par " + user, value=str(LogsObj.GetNbCmdUsedByCmdByUser("$wiibleyde",user)), inline=False)
        await message.channel.send(embed=embed)

    if message.content.startswith('$help'):
        LogsObj.AddLog(message.author.name,"$help")
        embed = discord.Embed(title="Commandes", description="Liste des commandes", color=0x00ff00)
        if message.author.name == AdminName:
            embed.add_field(name="$update", value="Mise à jour des données **(admin only)**", inline=False)
            embed.add_field(name="$statscmd", value="Statistiques des commandes **(admin only)**", inline=False)
            embed.add_field(name="$statscmdbyuser", value="Statistiques des commandes par utilisateur **(admin only)**", inline=False)
        embed.add_field(name="$next", value="Prochain évènement", inline=False)
        embed.add_field(name="$week", value="Evènements de la semaine", inline=False)
        embed.add_field(name="$wiibleyde", value="Wiibleyde", inline=False)
        embed.add_field(name="$stats", value="Statistiques", inline=False)
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
            showerfunc("Waiting " + str(30-count) + " minutes")
        cal=parse_ical()
        event=getNextEvent(cal)
        timeleft=CalcTimeLeft(event)
        # showerfunc("Next event in : " + str(timeleft) + " : " + event.get('summary') + " : " + getEventDate(event).strftime("%d/%m/%Y %H:%M:%S"))
        # showerfunc("Reload status")
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
        showerfunc("Calendar downloaded")
    except:
        showerfunc("Error downloading calendar")
        sys.exit(1)

def parse_ical():
    try:
        cal = icalendar.Calendar.from_ical(open('calendar.ics', 'rb').read())
        return cal
    except:
        showerfunc("Error parsing calendar")
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

def showerfunc(message):
    """Print a message to showerfunc
    
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
        showerfunc("Calendar deleted")
    except:
        showerfunc("Error deleting calendar")

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
    LogsObj=Database("logs.db")
    LogsObj.CreateDB()
    delete_ical()
    download_ical()
    client.run(BotToken)