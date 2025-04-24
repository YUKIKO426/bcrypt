# Telegram Voice Chat Recording Player
# For py-tgcalls version 2.1.1 and pyrogram 2.x

import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pyrogram.idle import idle

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Telegram credentials
API_ID = 23435637  # Replace with your API ID
API_HASH = "9263b0daadad72c094dc6977439b43e8"  # Replace with your API Hash

# Your control group ID (where commands will be sent from)
CONTROL_GROUP_ID = -1002449164321

# Commands
PLAY_COMMAND = "!play"
JOIN_COMMAND = "!join"
LEAVE_COMMAND = "!leave"

# Initialize Pyrogram and PyTgCalls clients
app = Client("voice_player_userbot", api_id=API_ID, api_hash=API_HASH)
pytgcalls = PyTgCalls(app)

# State tracking
active_calls = {}
downloaded_files = {}

@app.on_message(filters.command("start", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def start_command(client, message: Message):
    await message.reply(
        "Voice Chat Player is active!\n\n"
        f"Commands:\n"
        f"• {JOIN_COMMAND} [group_id] - Join a voice chat\n"
        f"• {PLAY_COMMAND} [group_id] - Play last recorded voice chat\n"
        f"• {LEAVE_COMMAND} [group_id] - Leave voice chat\n"
        f"• !help - Show this message"
    )

@app.on_message(filters.command("help", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def help_command(client, message: Message):
    await message.reply(
        "Voice Chat Player Commands:\n\n"
        f"• {JOIN_COMMAND} [group_id] - Join a voice chat\n"
        f"• {PLAY_COMMAND} [group_id] - Play last recorded voice chat\n"
        f"• {LEAVE_COMMAND} [group_id] - Leave voice chat\n\n"
        f"Example:\n"
        f"{JOIN_COMMAND} -1001987654321\n"
        f"{PLAY_COMMAND} -1001987654321"
    )

@app.on_message(filters.command("join", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def join_voice_chat(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2:
            return await message.reply("Please provide a target group ID. Example: !join -1001234567890")
        target_group = int(args[1])
        if target_group in active_calls:
            return await message.reply(f"Already in voice chat in group {target_group}")

        await pytgcalls.join_group_call(target_group, AudioPiped("silent.mp3"))
        active_calls[target_group] = True
        await message.reply(f"Joined voice chat in group {target_group}")
    except Exception as e:
        logger.error(f"Error joining voice chat: {e}")
        await message.reply(f"Failed to join voice chat: {str(e)}")

@app.on_message(filters.command("leave", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def leave_voice_chat(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2:
            return await message.reply("Please provide a target group ID. Example: !leave -1001234567890")
        target_group = int(args[1])
        if target_group not in active_calls:
            return await message.reply(f"Not in a voice chat in group {target_group}")

        await pytgcalls.leave_group_call(target_group)
        del active_calls[target_group]
        await message.reply(f"Left voice chat in group {target_group}")
    except Exception as e:
        logger.error(f"Error leaving voice chat: {e}")
        await message.reply(f"Failed to leave voice chat: {str(e)}")

@app.on_message(filters.voice & filters.chat(CONTROL_GROUP_ID))
async def handle_voice_message(client, message: Message):
    try:
        voice_file = await message.download()
        downloaded_files["last_voice"] = voice_file
        await message.reply(
            "Voice message downloaded and ready to play.\n"
            f"Use '{PLAY_COMMAND} [group_id]' to play it in a target group."
        )
    except Exception as e:
        logger.error(f"Error downloading voice message: {e}")
        await message.reply(f"Failed to download voice message: {str(e)}")

@app.on_message(filters.command("play", prefixes="!") & filters.chat(CONTROL_GROUP_ID))
async def play_voice_chat(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2:
            return await message.reply("Please provide a target group ID. Example: !play -1001234567890")
        target_group = int(args[1])
        if "last_voice" not in downloaded_files:
            return await message.reply("No voice message available. Please send one first.")
        voice_file = downloaded_files["last_voice"]

        if target_group not in active_calls:
            await pytgcalls.join_group_call(target_group, AudioPiped(voice_file))
            active_calls[target_group] = True
            await message.reply(f"Joined and playing in group {target_group}")
        else:
            await pytgcalls.change_stream(target_group, AudioPiped(voice_file))
            await message.reply(f"Playing new recording in group {target_group}")
    except Exception as e:
        logger.error(f"Error playing voice chat: {e}")
        await message.reply(f"Failed to play voice chat: {str(e)}")

@pytgcalls.on_stream_end()
async def on_stream_end(client, update):
    logger.info(f"Stream ended in {update.chat_id}")

async def create_silent_audio():
    if os.path.exists("silent.mp3"):
        return
    try:
        os.system('ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 1 -q:a 9 -acodec libmp3lame silent.mp3')
        logger.info("Created silent.mp3")
    except Exception as e:
        logger.error(f"Could not create silent.mp3: {e}")

async def main():
    await create_silent_audio()
    await app.start()
    await pytgcalls.start()
    print("Bot started. Send !start in the control group.")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
