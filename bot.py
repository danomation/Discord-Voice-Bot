
import openai
import discord
from gtts import gTTS
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get
from elevenlabslib.helpers import *
from elevenlabslib import *
from elevenlabs import generate, save

##
# Project GPT-Voice
# May not Work! VERY basic and buggy use at your own risk and NOT in production!
#
# Danomation
# GitHub: https://github.com/danomation
# Personal Site: sussyvr.com
# Patreon https://www.patreon.com/Wintermute310
# I'm broke as hell please donate xd
##

# instructions: Add your openai api key and bot api token
# set the target channel id for where to ask it questions with "!GPT message here"
openai.api_key = "OPENAI API Key"
elevenlabs_api_key = "Elevenlabs API Key"
discord_api_token = 'Your Discord Bot Token'
discord_target_channel_id = "Which discord channel id do you wanna use? Add it here without quotes"

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
        {"role": "system", "content": "You're a very sassy robot. You answer questions in 127 characters or less"},
        {"role": "user", "content": cookedmessage}
        ],
        temperature=1.2,
        max_tokens=1024,
        user = author
    )
    text = str(response['choices'][0]['message']['content'])
    return text


def sendtts(message):
    ## google tts option
    #tts = gTTS(message, tld='co.uk')
    #tts.save("./1.mp3")
    #return "./1.mp3"

    ##begin test of elevenlabs
    audio = generate(
    text=message,
    voice="Rachel",
    )
    save(audio, "./2.mp3")
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
    source = FFmpegPCMAudio(sendtts(sendgpt(str(ctx.message.content), str(ctx.message.author))))
    try:
        voice.play(source)
    except:
        await ctx.message.reply("Wait a few...")


bot.run(discord_api_token)
