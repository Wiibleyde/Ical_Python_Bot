# ICal-checker
This program made in python allows you (by giving the url of a `.ics` calendar) to ask it what is the next event and the time between you and it.

## Setup
For proper operation, you need to create a python bot **not a webhook**.  

When you have the token of your discord bot, remember to activate (in the Discord API) the fact that the bot can read the messages of the channels of a server.  

Remember to fill in the right variables in the python code with the mandatory data for the proper functioning.  

This program needs non-native python libraries : discord, os, requests, icalendar, datetime, pytz, sys, asyncio

To install them, you can use the command pip command : 
```
pip install discord.py icalendar pytz asyncio
```

## Usage
To launch the program, you can use the command :  
On Windows : 
```
python main.py
```

The bot won't print anything in the console, but you can see the logs in the stderr.

## Commands
The bot has 2 commands :  
`$next` : This command will print the next event of the calendar. 
`$week` : This command will print the next days with events in the calendar.
`$help` : This command will print the help message.

## License
You can use this code for your own project, but you have to credit me as the author of the code *(Wiibleyde)*.

## Contact
If you have any questions, you can contact me on Discord : `Wiibleyde#2834`
