#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, azlyrics, logging, time, asyncio
from telethon import TelegramClient, events, utils, Button
from enum import Enum, auto

def get_env(name, message, cast=str):
    logger = logging.getLogger('system.getenv')
    if name in os.environ:
        return os.environ[name]
    while True:
        value = input(message)
        try:
            return cast(value)
        except ValueError as e:
            logger.exception(e)
            time.sleep(1)

session = get_env('TG_SESSION_NAME', 'Enter a session name:')
api_id = get_env('TG_API_ID', 'Enter your API ID: ')
api_hash = get_env('TG_API_HASH', 'Enter your API hash: ')
bot_token = get_env('TG_BOT_TOKEN', 'Enter your Bot Token if using bot: ')
bot = TelegramClient(session, api_id, api_hash).start(bot_token=bot_token)

helpText = "This bot is aimed to find lyrics to a song and print it out for you. **Commands are in below:** \n\n" \
            "1. /help - Prints out this help text\n" \
            "2. /start - Starts the bot\n" \
            "3. /stop - Stops the bot\n\n" \
            "4. `Lyrics of a song` - After this command, user must enter both artist and song spelled correctly to get the lyrics of it directly. " \
            "Name of the artist and song should be separated with an hyphen (-). \n__Example input:__ **Oasis - Don't Look Back in Anger**\n\n" \
            "5. `Search by lyrics` - After this command, user must enter the lyrics that he/she remembers partially. " \
            "If only one result with these lyrics found, then it will be printed out. If multiple results are found, first five result will " \
            "be printed out and user will choose the correct one if it is listed. If it is not listed, user may proceed with the next five results and so on.\n\n" \
            "6. `Songs of artist` - After this command, user must enter the name of the artist to retrieve all songs of belonging to it. " \
            "Only songs that have lyrics will be shown. User will be able to choose the song with its number. If song list is too long, it will be paginated.\n\n" \
            "7. `Albums of artist` - After this command, user must enter the name of the artist to retrieve the album names " \
            "that have songs with lyrics in them."

class State(Enum):
    LYRICS_OF = auto()
    SEARCH_BY = auto()
    SONGS_OF = auto()
    ALBUMS_OF = auto()
    STOP_BOT = auto()
    START_BOT = auto()

conversation_state = {}

# [1] Above class and conversation_state must be used because bot.conversation does not work as intended.
# [1] Refer to: https://stackoverflow.com/a/64213961 and https://stackoverflow.com/a/62246569

buttonOptions = [
    [
        Button.inline("Cancel ❌", data='cancel'),
        Button.inline("Next ➡️", data='next')
    ],
    [
        Button.inline("Show the lyrics! ✅", data='show'),
    ]
]

class SearchResultIterator:
    # An example return is:
    # ('1', ['Song - Artist', " ... lyrics result ... ", 'https://www.azlyrics.com/lyrics/artist/song.html'])
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.currentIndex = 0
        self.keys = list(dictionary.keys())
    
    def getNext(self):
        if self.currentIndex < len(self.keys) - 1:
            self.currentIndex += 1
            key = self.keys[self.currentIndex]
            return key, self.dictionary[key]
        else:
            raise StopIteration
    
    def getCurrent(self):
        if self.currentIndex < len(self.keys):
            key = self.keys[self.currentIndex]
            return key, self.dictionary[key]
        else:
            return None

@bot.on(events.NewMessage(pattern='/help'))
async def help(event):
    who = event.sender_id
    logger = logging.getLogger('events.help')
    logger.debug(str(who) + " asked for help, state is " + str(conversation_state.get(who)))
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT:
        await bot.send_message(event.chat_id, 'Please type /start or click the button to start using the bot.', buttons=Button.text("Start", resize=True, single_use=True))
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        await event.respond(helpText)
        raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='/start|[sS]tart'))
async def start(event):
    who = event.sender_id
    logger = logging.getLogger('events.start')
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.START_BOT
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        menu = [
            [
                Button.text("Lyrics of a song", resize=True),
                Button.text("Search by lyrics", resize=True)
            ],
            [
                Button.text("Songs of artist", resize=True),
                Button.text("Albums of artist", resize=True)
            ]
        ]
        await bot.send_message(event.chat_id, '🏁 Bot Started 🏁\nChoose an option from the menu or type /help', buttons=menu)
        raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='/stop'))
async def stop(event):
    who = event.sender_id
    logger = logging.getLogger('events.stop')
    if conversation_state.get(who) != State.STOP_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.STOP_BOT
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        await bot.send_message(event.chat_id, '🛑 Bot Stopped 🛑', buttons=Button.text("Start", resize=True, single_use=True))
        raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='Lyrics of a song'))
async def lyricsof(event):
    who = event.sender_id
    logger = logging.getLogger('events.lyricsofasong') # Set the logger
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT: # Check if state is START_BOT
        await event.respond("Please type /start or click the button to start using the bot.")
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.LYRICS_OF
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("Enter both artist and song name spelled correctly. \nThey should be separated with an hyphen (-)")
            try:
                response = await conv.get_response(timeout=90)
                lyricsof = response.text
                if lyricsof == "/stop": # Immediately stop the bot when user types the command
                    raise events.StopPropagation
                elif not '-' in lyricsof: # Check if input contains hyphen
                    await event.respond('Please split the artist name and song name with an hyphen (-).\nExample: **Elton John - Please**')
                else:
                    try:
                        artistName, songName = lyricsof.split("-")
                    except ValueError: # Check if more than one hyphen (-) is entered
                        await conv.send_message('You did not sent a valid message.\nPlease split the artist name and song name with only one hyphen.\nExample: **Elton John - Please**')
                        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                        conversation_state[who] = State.START_BOT
                        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                        raise events.StopPropagation
                    l = azlyrics.lyrics(artistName, songName) # Get the lyrics OR sorry message
                    if "Search by lyrics" in l: # Check if response is sorry message
                        await event.respond(l)
                    else:
                        for lyrics in l: # Stringfy the lyrics which is a type of list
                            if len(lyrics) >= 4096: # Check if total number of chars is greater than 4096
                                # https://tl.telethon.dev/methods/messages/send_message.html <-->  MessageTooLongError
                                await event.respond("Lyrics are more than 4096 chars, can not be sent.\nThis issue will be fixed soon.")
                                logger.warning("4096 characters exception occurred. User could not get the result.")
                            else:
                                await event.respond("```" + lyrics + "```")
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
            except asyncio.TimeoutError: # Catch the timeout
                await conv.send_message("⌛ You are late to respond. Please send your message in ~90 seconds.")
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='Albums of artist'))
async def albumsof(event):
    who = event.sender_id
    logger = logging.getLogger('events.albumsofartist') # Set the logger
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT: # Check if state is START_BOT
        await event.respond("Please type /start or click the button to start using the bot.")
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.ALBUMS_OF
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("Enter the artist name.")
            try:
                response = await conv.get_response(timeout=90)
                albumsof = response.text
                if albumsof == "/stop": # Immediately stop the bot when user types the command
                    raise events.StopPropagation
                else:
                    a = azlyrics.albums(albumsof)
                    if "Sorry, I couldn't find any albums for" in a: # Check if response is sorry message
                        await event.respond(a)
                    else:
                        albums = '\n'.join(a) # Concatenate the albums which is a type of list
                        await event.respond(albums)
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
            except asyncio.TimeoutError: # Catch the timeout
                await conv.send_message("⌛ You are late to respond. Please send your message in ~90 seconds.")
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='Songs of artist'))
async def songsof(event):
    who = event.sender_id
    logger = logging.getLogger('events.songsofartist') # Set the logger
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT: # Check if state is START_BOT
        await event.respond("Please type /start or click the button to start using the bot.")
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.SONGS_OF
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("Enter the artist name.")
            try:
                response = await conv.get_response(timeout=90)
                songsof = response.text
                if songsof == "/stop": # Immediately stop the bot when user types the command
                    raise events.StopPropagation
                else:
                    s = azlyrics.songs(songsof)
                    if "Sorry, I couldn't find any songs for" in s: # Check if response is sorry message
                        await event.respond(s)
                    else:
                        for song in s:
                            songs = '\n'.join(s[song]) # Concatenate the songs which is a type of list
                            respond = "**" + song + "**\n" + songs # Final respond to the user with album + songs
                            await event.respond(respond)
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
            except asyncio.TimeoutError: # Catch the timeout
                await conv.send_message("⌛ You are late to respond. Please send your message in ~90 seconds.")
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='Search by lyrics'))
async def searchby(event):
    who = event.sender_id
    logger = logging.getLogger('events.searchbylyrics') # Set the logger
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT: # Check if state is START_BOT
        await event.respond("Please type /start or click the button to start using the bot.")
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.SEARCH_BY
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        async with bot.conversation(event.sender_id) as conv:
            await conv.send_message("Enter the lyrics that you know of.")
            try:
                response = await conv.get_response(timeout=90)
                searchby = response.text
                if searchby == "/stop": # Immediately stop the bot when user types the command
                    raise events.StopPropagation
                elif len(searchby) < 6 or len(searchby) > 100:
                    await event.respond("Length of the lyrics you entered must be more than 6 and less than 100 characters.")
                    conversation_state[who] = State.START_BOT
                else:
                    s = azlyrics.search(searchby)
                    if "Sorry, I couldn't find any songs for" in s: # Check if response is sorry message
                        await event.respond(s)
                        conversation_state[who] = State.START_BOT
                    elif "Could not get a valid response from server." in s: # Check if server not responding 
                        await event.respond(s)
                        conversation_state[who] = State.START_BOT
                    else:
                        await searchbyResponse(event, s)
            except asyncio.TimeoutError: # Catch the timeout
                await conv.send_message("⌛ You are late to respond. Please send your message in ~90 seconds.")
                logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
    raise events.StopPropagation

async def searchbyResponse(event, s):
    who = event.sender_id
    logger = logging.getLogger('events.searchbyresponse') # Set the logger
    logger.debug("State is " + str(conversation_state.get(who)) + " and sender is " + str(who))
    global ri
    ri = SearchResultIterator(s) # create an iterator for the search result
    riRes = ri.getCurrent() # get the first item
    sTitle = riRes[0] + ") " + riRes[1][0] # first item in iter + second item's (list) first item
    sLyrics = riRes[1][1]
    # sLink = riRes[1][2]
    sRes = "**" + sTitle + "**\n\n" + "```" + sLyrics + "```"
    await event.respond(sRes, buttons=buttonOptions)

@bot.on(events.CallbackQuery(data='next'))
async def searchNext(event):
    who = event.sender_id
    logger = logging.getLogger('events.searchbylyrics.searchNext') # Set the logger
    try:
        riRes = ri.getNext() # get the next item
    except StopIteration:
        await event.edit("You have reached the end of the results.")
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.START_BOT
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        raise events.StopPropagation
    else:
        sTitle = riRes[0] + ") " + riRes[1][0] # first item in iter + second item's (list) first item
        sLyrics = riRes[1][1]
        sRes = "**" + sTitle + "**\n\n" + "```" + sLyrics + "```"
        await event.edit(sRes, buttons=buttonOptions)
        raise events.StopPropagation

@bot.on(events.CallbackQuery(data='show'))
async def searchShow(event):
    who = event.sender_id
    logger = logging.getLogger('events.searchbylyrics.searchShow') # Set the logger
    riRes = ri.getCurrent() # get the result
    sTitle = "**" + riRes[0] + ") " + riRes[1][0] + "**" # first item in iter + second item's (list) first item
    sLink = riRes[1][2]
    l = azlyrics.lyricsFromUrl(sLink)
    for lyrics in l: # Stringfy the lyrics which is a type of list
        if len(lyrics) >= 4096: # Check if total number of chars is greater than 4096
            # https://tl.telethon.dev/methods/messages/send_message.html <-->  MessageTooLongError
            await event.edit("Lyrics are more than 4096 chars, can not be sent.\nThis issue will be fixed soon.")
            logger.warning("4096 characters exception occurred. User could not get the result.")
        else:
            await event.edit(sTitle + "```" + lyrics + "```")
    # Move back to START_BOT state
    logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
    conversation_state[who] = State.START_BOT
    logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
    raise events.StopPropagation

@bot.on(events.CallbackQuery(data='cancel'))
async def searchCancel(event):
    who = event.sender_id
    logger = logging.getLogger('events.searchbylyrics.searchCancel') # Set the logger
    await event.edit("Search is cancelled.\nChoose an option from the menu or type /help")
    logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
    conversation_state[who] = State.START_BOT
    logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
    raise events.StopPropagation

@bot.on(events.NewMessage(incoming=True))
async def allother(event):
    who = event.sender_id
    logger = logging.getLogger('events.allother')
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT:
        logger.debug("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.STOP_BOT
        logger.debug("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        await bot.send_message(event.chat_id, 'Please type /start or click the button to start using the bot.', buttons=Button.text("Start", resize=True, single_use=True))
        raise events.StopPropagation
    logger.debug("I am at the very beginning. State is " + str(conversation_state.get(who)) + " and sender is " + str(who))
    if conversation_state[who] == State.START_BOT:
        await event.respond("Type /help to get help.")
        raise events.StopPropagation

def main():
    logging.basicConfig(format='[%(asctime)s](%(levelname)s) %(name)s: %(message)s',
                        filename='kasetlyrics.log', level=logging.DEBUG)
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()
