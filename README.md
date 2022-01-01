# Lyrics Bot for Telegram

This is a Telegram bot which is able to find lyrics to a song and print it out for the user. It uses [Telethon](https://github.com/LonamiWebs/Telethon) which is a *pure Python 3 MTProto API Telegram client library*. Lyrics are retrieved from [azlyrics.com](https://azlyrics.com) by web scraping method. `azlyrics.py` is a modified file that is inspired from [adhorrig/azlyrics](https://github.com/adhorrig/azlyrics)

My own version is [KasetLyricsBot](https://t.me/KasetLyricsBot), free for all.

## Commands / Options

1. `/help` - Prints out the help text
2. `/start` - Starts the bot
3. `/stop` - Stops the bot
4. `Lyrics of a song` - After this option, user must enter both artist and song spelled correctly to get the lyrics of it directly. Name of the artist and song should be separated with an hyphen (-).<br> *Example input:* **Oasis - Don't Look Back in Anger**
5. `Search by lyrics` - After this option, user must enter the lyrics that he/she remembers partially. If only one result with these lyrics found, then it will be printed out. If multiple results are found, first five result will be printed out and user will choose the correct one if it is listed. If it is not listed, user may proceed with the next five results and so on.
6. `Songs of artist` - After this option, user must enter the name of the artist to retrieve all songs of belonging to it. Only songs that have lyrics on the database will be shown. User will be able to choose the song with its number. If song list is too long, it will be paginated.
7. `Albums of artist` - After this option, user must enter the name of the artist to retrieve the album names that have songs with lyrics in them.

## TODO

- [x] Use menu ([buttons](https://docs.telethon.dev/en/latest/modules/custom.html?highlight=Button#module-telethon.tl.custom.button)) options instead of commands.
- [x] `Lyrics of a song`
- [ ] `Search by lyrics`
- [ ] `Songs of artist`
- [x] `Albums of artist`
- [ ] Fix [MessageTooLongError](https://tl.telethon.dev/methods/messages/send_message.html) where messages longer than 4096 characters can not be sent.
- [x] Better logging mechanism.
- [ ] Print the Spotify link of the song after the request.
- [ ] Find by Spotify link: User pastes the link and lyrics are displayed.
- [ ] `Delete Me` option, where the user can delete his/her `sender_id` from `conversation_state` array.

> If the number of users increases, a database might be used to store `conversation_state` for each user.

## Requirements for Development

To install the requirements, run:

`pip3 install -r requirements.txt`

You can prepare a file called `exportapi.sh` to easily export your API information for continuous development. An example is in below:

```
export TG_SESSION_NAME=nameOfYourSession
export TG_API_ID=1234567
export TG_API_HASH=yourPers0nalApiHashThatY0uG3tFr0mTelegram
export TG_BOT_TOKEN=1234567890:yourB0tTokenThatY0uG3tFr0mBotFather
```

To export this in your current shell, run `chown 700 exportapi.sh && . exportapi.sh`

### Command List to send to the BotFather
Below is the command list that you can send to the [BotFather](https://t.me/BotFather). This is done for the users that are going to use your bot.

```
help - See how to use this bot
start - Start the bot
stop - Stop the bot
```

### Run
```
python3 kasetlyricsbot.py
```
