import os
import openai
import discord
import time
from gtts import gTTS
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get
from elevenlabs import set_api_key
from elevenlabs import generate, save
import requests
import json
import asyncio

##
# Danomation
# GitHub: https://github.com/danomation
# Patreon https://www.patreon.com/Wintermute310
##

#api keys
openai.api_key = ""
OPEN_WEATHER_MAP_APIKEY = ''
elevenlabs_api_key = ""
set_api_key(elevenlabs_api_key)
discord_api_token = ''

#discord bot settings
bot_name = "GPT-Voice"
discord_target_channel_id = channelidhere
voice_admin = useridhere
#path for temporary mp3 files
temp_path = "./"
prefix = "!"
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, intents=intents)

#set your default tts provider
#e.g. tts_provider = "google" or "elevenlabs"
tts_provider = "google"


def get_current_weather(location):
    """Get the current weather in a given location"""
    url = "http://api.openweathermap.org/geo/1.0/direct?q=" + location + "&limit=1&appid=" + OPEN_WEATHER_MAP_APIKEY + ""
    res = requests.get(url)
    data = res.json()
    #data = json.dumps(data)
    lat = str(data[0]["lat"])
    lon = str(data[0]["lon"])
    url = "https://api.openweathermap.org/data/2.5/weather?lat=" + lat + "&lon=" + lon + "&appid=" + OPEN_WEATHER_MAP_APIKEY + "&units=imperial"
    res = requests.get(url)
    data = res.json()
    print(data)
    humidity = data['main']['humidity']
    pressure = data['main']['pressure']
    wind = data['wind']['speed']
    description = data['weather'][0]['description']
    temp = data['main']['temp']
    weather_info = {
        "location": location,
        "temperature": temp,
        "humidity": humidity,
        "pressure": pressure,
        "wind speed": wind,
        "unit": "fahrenheit",
        "description": description,
    }
    return json.dumps(weather_info)


def sendgpt(message, author):
    rawmessage = message.lower()
    rawmessage = rawmessage.split("!gpt")
    cookedmessage = ""
    for rawmsg in rawmessage:
        cookedmessage += rawmsg
    messages = [
        {"role": "system",
         "content": "Your name is" + bot_name + ". Reply Limit is 70 words. Don't use Hashtags or emojis. If the user asks who they are reply with " + author + "."},
        {"role": "user", "content": cookedmessage}
    ]
    functions = [
        {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city, e.g. San Francisco",
                    },
                },
                # "required": ["location"],
            },
        },
    ]
    chat = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        functions=functions,
        temperature=1.2,
        max_tokens=1024,
        user=author
    )
    convo = chat["choices"][0]["message"]
    # check if the conversation included a function call
    if convo.get("function_call"):
        available_functions = {
            "get_current_weather": get_current_weather,
        }
        # run function (adapted from openai's docs example)
        function_name = convo["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(convo["function_call"]["arguments"])
        function_response = function_to_call(
            # set location to the function args for location
            location=function_args.get("location"),
        )
        # add the function response to the conversation
        messages.append(convo)
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        )
        # wrap the conversation with the function call in a new conversation.
        chat = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            functions=functions,
            temperature=1.2,
            max_tokens=1024,
            user=author,
        )
    return str(chat["choices"][0]["message"]["content"])


def sendtts(message):
    time_stamp = str(time.time())
    #set file path
    file_path = temp_path + "reply_" + time_stamp + ".mp3"
    if tts_provider == "elevenlabs":
        print(message)
        audio = generate(
        text=message,
        voice="Rachel",
        model="eleven_monolingual_v1"
        )
        save(audio, file_path)
        return file_path
    else:
        tts = gTTS(message, tld='co.uk')
        tts.save(file_path)
        return file_path


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
    think = await ctx.send("thinking...")
    if voice.is_playing() == False:
        try:
            async with channel.typing():
                reply = sendgpt(str(ctx.message.content), str(ctx.message.author.display_name))
                file_path = sendtts(str(reply))
                source = FFmpegPCMAudio(file_path)
                voice.play(source)
                await ctx.message.reply("Replying with: " + reply)
                await ctx.send(file=discord.File(file_path))
        except:
            raise
    else:
        holdup = await ctx.message.reply("Wait a few...")
        await asyncio.sleep(3)
        await holdup.delete()
    if voice.is_playing() == False:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print("File could not be deleted")
    await think.delete()

@bot.command(
    name='elevenlabs',
    description='sends elevenlabs voice reply from gpt',
    pass_context=True,
)
async def elevenlabs(ctx):
    if ctx.message.author.id == voice_admin:
        global tts_provider
        tts_provider = "elevenlabs"
        await ctx.message.reply("Changed TTS to ElevenLabs")
    else:
        await ctx.message.reply("Unauthorized.")


@bot.command(
    name='google',
    description='sends elevenlabs voice reply from gpt',
    pass_context=True,
)
async def google(ctx):
    if ctx.message.author.id == voice_admin:
        global tts_provider
        tts_provider = "google"
        await ctx.message.reply("Changed to Google TTS")
    else:
        await ctx.message.reply("Unauthorized.")

bot.run(discord_api_token)
