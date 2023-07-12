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
from googleapiclient.discovery import build
import requests
import json
import asyncio
from bs4 import BeautifulSoup
import cloudscraper


##
# Danomation
# GitHub: https://github.com/danomation
# Patreon https://www.patreon.com/Wintermute310
##

#api keys
openai.api_key = ""
OPEN_WEATHER_MAP_APIKEY = ""
elevenlabs_api_key = ""
set_api_key(elevenlabs_api_key)
discord_api_token = ""
GOOGLE_SEARCH_APIKEY = ""
GOOGLE_SEARCH_ENGINE_ID = ""

#discord bot settings
bot_name = "GPT-Voice"
discord_target_channel_id = your_voicechannel_id
voice_admin = your_discord_user_id
#path for temporary mp3 files
temp_path = "./"
prefix = "!"
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, intents=intents)

#set your default tts provider
#e.g. tts_provider = "google" or "elevenlabs"
#or use !google or !elevenlabs commands in voice chat
tts_provider = "google"


##
#  GPT-4 Functions
#
# Helper functions (summarize, scrape)
# summarize is what you expect, it summarizes text for the pages on Google
def summarize(search, result):
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role" : "system", "content" : "You summarize text with 50 word limit. emphasis on information on " + search + ""},
        {"role" : "user", "content": str(result)}
        ],
        temperature=1.2,
        max_tokens=1024,
    )
    text = response['choices'][0]['message']['content']
    return text

# scrape does the heavy lifting to find information from the sites from the Google search results
def scrape(search, link):
    scraper = cloudscraper.create_scraper(delay=10, browser='chrome')
    url = link
    info = scraper.get(url).text
    soup = BeautifulSoup(info, 'html.parser')
    index = 0
    result = []
    for para in soup.find_all("p"):
        result += [para.get_text()]
        index += 1
        if index == 10:
            break
        print(para)
    text = summarize(search, result)
    return(text)


# actual gpt funcs
# 1. get current weather anywhere
def get_current_weather(search, location):
    """Get the current weather in a given location"""
    url = "http://api.openweathermap.org/geo/1.0/direct?q=" + location + "&limit=1&appid=" + OPEN_WEATHER_MAP_APIKEY + ""
    res = requests.get(url)
    data = res.json()
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


#DISCLAIMER!! get permission from site owners!
# 2. search google and return results
def get_google_search(search, location):
    """Find the google search results"""
    service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_APIKEY)
    res = service.cse().list(q=search, cx=GOOGLE_SEARCH_ENGINE_ID, num=3).execute()
    results = res['items']
    searches = []
    for result in results:
        title = result['title']
        link = "<" + result['link'] + ">"
        summary = json.dumps(scrape(search, result['link']))
        print(summary)
        searches.append({
            "link": link,
            #"title": title,
            "summary": summary,
        })
    return json.dumps(searches)


#calls gpt, functions, and wraps it in another call
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
        {
            "name": "get_google_search",
            "description": "Searches the web and returns details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search values",
                    },
                },
                # "required": ["search"],
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
            "get_google_search": get_google_search,
        }
        # run function (adapted from openai's docs example)
        function_name = convo["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(convo["function_call"]["arguments"])
        function_response = function_to_call(
            # set args to the function args
            location=function_args.get("location"),
            search=function_args.get("search"),
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
        model="eleven_monolingual_v1",
        )
        save(audio, file_path)
        return file_path
    else:
        tts = gTTS(message, tld='co.uk')
        tts.save(file_path)
        return file_path


@bot.event
async def on_message(message):
    contents = message.content
    await bot.process_commands(message)
    if "!tts" in contents:
        contents = contents.replace("!tts", "")
        # auto-detect voice channel
        channel = message.author.voice.channel
        if not channel:
            return
        voice = get(bot.voice_clients, guild=message.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        think = await message.reply("thinking...")
        if voice.is_playing() == False:
            try:
                async with channel.typing():
                    file_path = sendtts(str(contents))
                    source = FFmpegPCMAudio(file_path)
                    voice.play(source)
                    await message.reply("Speaking: " + contents)
                    await message.channel.send(file=discord.File(file_path))
            except:
                raise
        else:
            holdup = await message.reply("Wait a few...")
            await asyncio.sleep(3)
            await holdup.delete()
        if voice.is_playing() == False:
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                print("File could not be deleted")
        await think.delete()
    if "!gpt" in contents:
        contents = contents.replace("!gpt", "")
        # auto-detect voice channel
        channel = message.author.voice.channel
        if not channel:
            return
        voice = get(bot.voice_clients, guild=message.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        think = await message.reply("thinking...")
        if voice.is_playing() == False:
            try:
                async with channel.typing():
                    reply = sendgpt(str(contents), str(message.author.display_name))
                    file_path = sendtts(str(reply))
                    source = FFmpegPCMAudio(file_path)
                    voice.play(source)
                    await message.reply("Replying with: " + reply)
                    await message.channel.send(file=discord.File(file_path))
            except:
                raise
        else:
            holdup = await message.reply("Wait a few...")
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

connections = {}


@bot.command()
async def vtts(ctx):  
    await ctx.message.delete()
    voice = ctx.author.voice

    if not voice:
        await ctx.respond("You aren't in a voice channel!")
    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        vc = await voice.channel.connect()
    else:
        vc = voice_client
    connections.update({ctx.guild.id: vc})
    vc.start_recording(
        discord.sinks.MP3Sink(),
        vtts_after,
        ctx.channel,
    )
    await asyncio.sleep(4)
    vc.stop_recording()


async def vtts_after(sink: discord.sinks, channel: discord.TextChannel, *args):
    user_id = ""
    for user_id, audio in sink.audio_data.items():
        user_id = f"<@{user_id}>"
        with open("output.mp3", "wb") as f:
            f.write(audio.file.getbuffer())
    audio_file = open("./output.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = str(transcript.text)
    test = await channel.send("!tts" + " " + transcript)
    await asyncio.sleep(1)
    await test.edit(content=user_id + " asked: " + transcript)


@bot.command()
async def vgpt(ctx): 
    await ctx.message.delete()
    voice = ctx.author.voice
    if not voice:
        await ctx.respond("You aren't in a voice channel!")
    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        vc = await voice.channel.connect()
    else:
        vc = voice_client
    connections.update({ctx.guild.id: vc})
    vc.start_recording(
        discord.sinks.MP3Sink(),
        vgpt_after,
        ctx.channel,
    )
    await asyncio.sleep(5)
    vc.stop_recording()

async def vgpt_after(sink: discord.sinks, channel: discord.TextChannel, *args):
    user_id = ""
    for user_id, audio in sink.audio_data.items():
        user_id = f"<@{user_id}>"
        with open("output.mp3", "wb") as f:
            f.write(audio.file.getbuffer())
    audio_file = open("./output.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = str(transcript.text)
    test = await channel.send("!gpt" + " " + transcript)
    await asyncio.sleep(1)
    await test.edit(content=user_id + " asked: " + transcript)


bot.run(discord_api_token)
