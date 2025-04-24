import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
from pyrogram.idle import idle

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV configuration
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
SESSION_NAME = os.environ.get("SESSION_NAME", "voice_bot")
CONTROL_GROUP_ID = int(os.environ.get("CONTROL_GROUP_ID", -1001234567890))

# Commands
PLAY_COMMAND = "!play"
JOIN_COMMAND = "!join"
LEAVE_COMMAND = "!leave"

# Initialize Pyrogram and PyTgCalls
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)
pytgcalls = PyTgCalls(app)

active_calls = {}
downloaded_files = {}

@app.on_message(filters.command("start", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def start_command(client, message: Message):
    await message.reply(
        "Voice Chat Player is active!\n\n"
        f"Commands:\n"
        f"• {JOIN_COMMAND} [group_id] - Join voice chat\n"
        f"• {PLAY_COMMAND} [group_id] - Play last voice\n"
        f"• {LEAVE_COMMAND} [group_id] - Leave voice chat\n"
        f"• !help - Show this message"
    )

@app.on_message(filters.command("help", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def help_command(client, message: Message):
    await start_command(client, message)

@app.on_message(filters.command("join", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def join_voice_chat(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2:
            return await message.reply("Usage: !join -1001234567890")
        group_id = int(args[1])
        if group_id in active_calls:
            return await message.reply(f"Already in voice chat in {group_id}")
        await pytgcalls.join_group_call(
            group_id,
            AudioPiped("silent.mp3", HighQualityAudio())
        )
        active_calls[group_id] = True
        await message.reply(f"Joined voice chat in {group_id}")
    except Exception as e:
        logger.error(f"Join error: {e}")
        await message.reply(f"Failed to join: {e}")

@app.on_message(filters.command("leave", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def leave_voice_chat(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2:
            return await message.reply("Usage: !leave -1001234567890")
        group_id = int(args[1])
        if group_id not in active_calls:
            return await message.reply(f"Not in voice chat in {group_id}")
        await pytgcalls.leave_group_call(group_id)
        del active_calls[group_id]
        await message.reply(f"Left voice chat in {group_id}")
    except Exception as e:
        logger.error(f"Leave error: {e}")
        await message.reply(f"Failed to leave: {e}")

@app.on_message(filters.voice & filters.chat(CONTROL_GROUP_ID))
async def handle_voice_message(client, message: Message):
    try:
        voice_file = await message.download()
        downloaded_files["last_voice"] = voice_file
        await message.reply("Voice downloaded. Use !play [group_id] to play it.")
    except Exception as e:
        logger.error(f"Download error: {e}")
        await message.reply(f"Failed to download voice: {e}")

@app.on_message(filters.command("play", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def play_voice_chat(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2:
            return await message.reply("Usage: !play -1001234567890")
        group_id = int(args[1])
        if "last_voice" not in downloaded_files:
            return await message.reply("No voice saved. Send one first.")
        voice_file = downloaded_files["last_voice"]
        if group_id not in active_calls:
            await pytgcalls.join_group_call(
                group_id,
                AudioPiped(voice_file, HighQualityAudio())
            )
            active_calls[group_id] = True
            await message.reply(f"Joined and playing in {group_id}")
        else:
            await pytgcalls.change_stream(
                group_id,
                AudioPiped(voice_file, HighQualityAudio())
            )
            await message.reply(f"Changed stream in {group_id}")
    except Exception as e:
        logger.error(f"Playback error: {e}")
        await message.reply(f"Failed to play: {e}")

async def create_silent_audio():
    if not os.path.exists("silent.mp3"):
        os.system('ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 1 -q:a 9 -acodec libmp3lame silent.mp3')
        logger.info("Created silent.mp3")

async def main():
    await create_silent_audio()
    await app.start()
    await pytgcalls.start()
    print("Bot is running.")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
