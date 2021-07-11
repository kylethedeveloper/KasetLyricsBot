#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, azlyrics, logging, time, asyncio
from telethon import TelegramClient, events, utils, Button
from enum import Enum, auto

def get_env(name, message, cast=str):
    if name in os.environ:
        return os.environ[name]
    while True:
        value = input(message)
        try:
            return cast(value)
        except ValueError as e:
            print(e, file=sys.stderr)
            time.sleep(1)

session = get_env('TG_SESSION_NAME', 'Enter a session name:')
api_id = get_env('TG_API_ID', 'Enter your API ID: ')
api_hash = get_env('TG_API_HASH', 'Enter your API hash: ')
bot_token = get_env('TG_BOT_TOKEN', 'Enter your Bot Token if using bot: ')
bot = TelegramClient(session, api_id, api_hash).start(bot_token=bot_token)

helpText = "This bot is aimed to find lyrics to a song and print it out for you. **Commands are in below:** \n\n" \
            "1. /help - Prints out this help text\n" \
            "2. /start - Starts the bot\n" \
            "3. /stop - Stops the bot\n" \
            "4. `Lyrics of a song` - After this command, user must enter both artist and song spelled correctly to get the lyrics of it directly. " \
            "Name of the artist and song should be separated with an hyphen (-). \n__Example input:__ **Oasis - Don't Look Back in Anger**\n" \
            "5. `Search by lyrics` - After this command, user must enter the lyrics that he/she remembers partially. " \
            "If only one result with these lyrics found, then it will be printed out. If multiple results are found, first five result will " \
            "be printed out and user will choose the correct one if it is listed. If it is not listed, user may proceed with the next five results and so on.\n" \
            "6. `Songs of artist` - After this command, user must enter the name of the artist to retrieve all songs of belonging to it. " \
            "Only songs that have lyrics will be shown. User will be able to choose the song with its number. If song list is too long, it will be paginated.\n" \
            "7. `Albums of artist` - After this command, user must enter the name of the artist to retrieve the album names " \
            "that have songs with lyrics in them. *(Not so useful)*"

helpLyricsOf = "`/lyricsof` - After this command, user must enter both artist and song spelled correctly to get the lyrics of it directly. " \
                "Name of the artist and song should be separated with an hyphen (-). \n__Example input:__ **/lyricsof Oasis - Don't Look Back in Anger**"


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

@bot.on(events.NewMessage(pattern='/help'))
async def help(event):
    who = event.sender_id
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT:
        await event.respond("Please type /start or click the button to start using the bot.")
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        await event.respond(helpText)
        raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='/start|[sS]tart'))
async def start(event):
    who = event.sender_id
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT:
        print("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.START_BOT
        print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
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
    if conversation_state.get(who) != State.STOP_BOT:
        print("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.STOP_BOT
        print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        await bot.send_message(event.chat_id, '🛑 Bot Stopped 🛑', buttons=Button.text("Start", resize=True, single_use=True))
        raise events.StopPropagation
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='Lyrics of a song'))
async def lyricsof(event):
    who = event.sender_id
    if conversation_state.get(who) is None or conversation_state[who] == State.STOP_BOT:
        await event.respond("Please type /start or click the button to start using the bot.")
        raise events.StopPropagation
    elif conversation_state[who] == State.START_BOT:
        print("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.LYRICS_OF
        print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
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
                        print("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                        conversation_state[who] = State.START_BOT
                        print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                        raise events.StopPropagation
                    l = azlyrics.lyrics(artistName, songName) # Get the lyrics OR sorry message
                    if "/searchbylyrics" in l: # Check if response is sorry message
                        await event.respond(l)
                    else:
                        for resp in l: # Stringfy the lyrics which is a type of list
                            if len(resp) >= 4096: # Check if total number of chars is greater than 4096
                                # https://tl.telethon.dev/methods/messages/send_message.html <-->  MessageTooLongError
                                await event.respond("Lyrics is more than 4096 chars, can not be sent.\nThis issue will be fixed soon.")
                            else:
                                await event.respond("```" + resp + "```")
                print("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
            except asyncio.TimeoutError: # Catch the timeout
                await conv.send_message("⌛ You are late to respond. Please send your message in ~90 seconds.")
                print("State was " + str(conversation_state.get(who)) + " and sender is " + str(who))
                conversation_state[who] = State.START_BOT
                print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
                raise events.StopPropagation
    raise events.StopPropagation

# @bot.on(events.NewMessage(pattern='Albums of artist'))
# async def albumsof(event):
#     await event.respond()
#

@bot.on(events.NewMessage(incoming=True))
async def allother(event):
    who = event.sender_id
    if conversation_state.get(who) is None:
        print("None condition. State is " + str(conversation_state.get(who)) + " and sender is " + str(who))
        conversation_state[who] = State.STOP_BOT
        print("Setting state to " + str(conversation_state.get(who)) + " and sender is " + str(who))
        await bot.send_message(event.chat_id, 'Bot server restarted.\n🛑 Bot Stopped 🛑', buttons=Button.text("Start", resize=True, single_use=True))
        raise events.StopPropagation
    print("I am at the very beginning. State is " + str(conversation_state.get(who)) + " and sender is " + str(who))
    if conversation_state[who] == State.START_BOT:
        await event.respond("Type /help to get help.")
        raise events.StopPropagation

def main():
    # artistSong = input("Artist - Song: ")
    # if not '-' in artistSong:
    #     print('Please split the artist name and song name with an hyphen (-).\nExample: Elton John - Please')
    # else:
    #     artistName, songName = artistSong.split("-")
    #     # artistName = input("Artist name: ")
    #     # songName = input("Song name: ")
    #     # print(azlyrics.songs(artistName))
    #     print(azlyrics.lyrics(artistName, songName))

    logging.basicConfig(format='[%(asctime)s](%(levelname)s) %(name)s: %(message)s',
                        filename='kasetlyrics.log', level=logging.INFO)
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()
