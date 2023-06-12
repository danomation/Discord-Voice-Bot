
import openai
import discord
from gtts import gTTS
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get
from elevenlabs import generate, save
from elevenlabs import set_api_key

##
# Project GPT-Voice
# This python file takes in a command !gpt texthere, sends to gpt-4, then replies with elevenlabs
#
# May not Work! VERY basic and buggy use at your own risk and NOT in production!
#
# Danomation
# GitHub: https://github.com/danomation
# Personal Site: https://sussyvr.com
# Patreon https://www.patreon.com/Wintermute310
# I'm broke as hell please donate xd
##

# instructions: Add your openai api key and bot api token
# set the target channel id for where to ask it questions with "!GPT message here"
openai.api_key = "OPENAI API Key"
elevenlabs_api_key = "Elevenlabs API Key"
set_api_key(elevenlabs_api_key)
discord_api_token = 'Your Discord Bot Token'
discord_target_channel_id = "Which discord channel id do you wanna use? Add it here without quotes"

# set TTS provider. "elevenlabs" or "google" TTS (free)
tts_provider = "elevenlabs"

prefix = "!"
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, intents=intents)


def sendgpt(message, author):
    rawmessage = message.lower()
    rawmessage = rawmessage.split("!gpt")
    cookedmessage = ""
    for rawmsg in rawmessage:
        cookedmessage += rawmsg

    response = openai.ChatCompletion.create(
    #model = "gpt-3.5-turbo",
    model="gpt-4",
    messages = [
        {"role": "system", "content": "Your name is GPT Voice. You're a very sassy robot. You're replying to questions in discord in 127 characters or . Don't use Hashtags."},
        {"role": "user", "content": cookedmessage}
        ],
        temperature=1.2,
        max_tokens=1024,
        user = author
    )
    text = str(response['choices'][0]['message']['content'])
    return text


def sendtts(message):
    if tts_provider == "elevenlabs":
        audio = generate(
        text=message,
        voice="Rachel",
        )
        save(audio, "./2.mp3")
        return "./2.mp3"
    else:
        tts = gTTS(message, tld='co.uk')
        tts.save("./2.mp3")
        return "./2.mp3"

@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command(
    name='gpt',
    description='Replies to your questions in Voice Chat',
    pass_context=True,
)
async def gpt(ctx):
    #only handle text from the GPT-Voice channel
    if ctx.message.channel.id != discord_target_channel_id:
        return
    #auto-detect voice channel
    channel = ctx.message.author.voice.channel
    if not channel:
        await ctx.send("You are not connected to a voice channel")
        return
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    print(ctx.message.content)
    reply = sendgpt(str(ctx.message.content), str(ctx.message.author))
    source = FFmpegPCMAudio(sendtts(reply))
    try:
        voice.play(source)
        await ctx.message.reply("Replying with: " + reply)
    except:
        await ctx.message.reply("Wait a few...")


bot.run(discord_api_token)
