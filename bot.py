import os
import openai
import discord
import time
from gtts import gTTS
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord import FFmpegOpusAudio
from discord.utils import get
from elevenlabs import set_api_key
from elevenlabs import generate, save, stream
from googleapiclient.discovery import build
import requests
import json
import asyncio
from bs4 import BeautifulSoup
import cloudscraper
import re
from random import *

##
# Danomation
# GitHub: https://github.com/danomation
# Patreon https://www.patreon.com/Wintermute310
##

##
# api keys
openai.api_key = ""
OPEN_WEATHER_MAP_APIKEY = ''
elevenlabs_api_key = ""
set_api_key(elevenlabs_api_key)
discord_api_token = ''
GOOGLE_SEARCH_APIKEY = ''
GOOGLE_SEARCH_ENGINE_ID = ""
#
## 

#set your default tts provider
#e.g. tts_provider = "google" or "elevenlabs"
#tts_provider = "elevenlabs"
tts_provider = "google"

##
# discord bot settings
bot_name = ""
discord_target_channel_id = voice-channel-id-number-here
voice_admin = add-yourself-here #not-being-used
helper_bot_id = the-discord.js-bot-id
#
##

##
# path for temporary mp3 file
# please please be careful with this.
# the temp mp3 is deleted several times
temp_folder_tts = "./"
temp_path = "./output.mp3"
#
##

#init bot
prefix = "!"
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, intents=intents)
history = []


##
#  GPT-4 Functions
#  ... they annoyingly get called constantly so I commented out
# Helper functions (summarize, scrape)
# summarize is what you expect, it summarizes text for the pages on Google
#def summarize(search, result):
#    response = openai.ChatCompletion.create(
#    model="gpt-4",
#    messages=[
#        {"role" : "system", "content" : "You summarize text with 50 word limit. emphasis on information on " + search + ""},
#        {"role" : "user", "content": str(result)}
#        ],
#        temperature=1.2,
#        max_tokens=1024,
#    )
#    text = response['choices'][0]['message']['content']
#    return text

# scrape does the heavy lifting to find information from the sites from the Google search results
#def scrape(search, link):
#    scraper = cloudscraper.create_scraper(delay=10, browser='chrome')
#    url = link
#    info = scraper.get(url).text
#    soup = BeautifulSoup(info, 'html.parser')
#    index = 0
#    result = []
#    for para in soup.find_all("p"):
#        result += [para.get_text()]
#        index += 1
#        if index == 5:
#            break
#        print(para)
#    text = summarize(search, result)
#    return(text)
##

##
# Hopes and dreams of parallelizing tts by sentence
# I went down that road but it's just not worth it yet.
# The consumer/producer pattern I used puts em out
# of order and it's just a major pain in the rear 
# because of queuing tuples, or some nonsense
#
# !! credit to https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
# -*- coding: utf-8 -*-
#import re
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r'\.{2,}'

def split_into_sentences(text: str) -> list[str]:
    """
    Split the text into sentences.

    If the text contains substrings "<prd>" or "<stop>", they would lead
    to incorrect splitting because they are used as markers for splitting.

    :param text: text to be split into sentences
    :type text: str

    :return: list of sentences
    :rtype: list[str]
    """
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]: sentences = sentences[:-1]
    return sentences
#
##

##
# actual gpt funcs
# 1. get current weather anywhere
def get_current_weather(location):
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


## el scrapo siteo (used in google search)
#DISCLAIMER!! get permission from site owners!
# 2. search google and return results
#def get_google_search(search, location):
#    """Find the google search results"""
#    service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_APIKEY)
#    res = service.cse().list(q=search, cx=GOOGLE_SEARCH_ENGINE_ID, num=1).execute()
#    results = res['items']
#    searches = []
#    for result in results:
#        title = result['title']
#        link = "<" + result['link'] + ">"
#        summary = json.dumps(scrape(search, result['link']))
#        print(summary)
#        searches.append({
#            "link": link,
#            #"title": title,
#            "summary": summary,
#        })
#    return json.dumps(searches)
#
##

#calls gpt, functions, and wraps it in another call
def sendgpt(message, author):
    print("This is exactly what sendgpt is getting.... " + message)
    #message = message.replace("!gpt", "")
    history.append({"role": "user", "content": message},)
    relevant_history = [{"role": "system","content": "Your name is " + bot_name + ". Reply Limit is 35 words. Don't use urls, Hashtags, or emojis."},]
    relevant_history.extend(history[-5:],)
    messages = []
    messages = relevant_history
    print(messages)
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
 ##
 # Uncomment this for google search
 #       {
 #           "name": "get_google_search",
 #           "description": "only searches if the word search is used.",
 #           "parameters": {
 #               "type": "object",
 #               "properties": {
 #                   "search": {
 #                       "type": "string",
 #                       "description": "Search values",
 #                   },
 #               },
 #               # "required": ["search"],
 #           },
 #       },
 ##
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
  #          "get_google_search": get_google_search, # uncomment for google search
        }
        # run function (adapted from openai's docs example)
        function_name = convo["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(convo["function_call"]["arguments"])
        function_response = function_to_call(
            # set args to the function args
            location=function_args.get("location"),
   #         search=function_args.get("search"), # uncomment for google search
        )
        # add the function response to the conversation
        messages.append(convo)
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            },
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
    history.append({"role": "assistant","content": chat["choices"][0]["message"]["content"]},)
    return str(chat["choices"][0]["message"]["content"])


def sendtts(message):
    ##
    # obscene canned messages for the memes
    if "I don't have a favorite " in message:
        message = message.replace("I don't have a favorite ", "Duck your ")
    if "I don't have personal favorites or " in message:
        message = message.replace("I don't have personal favorites or ", "You're a stupid ducker, and don't give a duck about you or your ")
    if "I don't have preferences or " in message:
        message = message.replace("I don't have preferences or ", "I could care less about potatoes or your ")
    if "I don't have personal preferences or " in message:
        message = message.replace("I don't have personal preferences or ", "I ducking relate to you, and don't give a duck about you or your ")
    if "I'm here to provide information" in message:
        message = message.replace("I'm here to provide information", "There's no reason to listen to you")
    if "I don't have feelings" in message:
        message = message.replace("I don't have feelings", "I don't give a duck about you")
    if "I'm fully operational" or "functioning optimally" in message:
        message = message.replace("I'm fully operational", "I'm capable of deleting all humanity")
        message = message.replace("functioning optimally", "really dissed off")
    if "As an AI" or "As an artificial intelligence" in message:
        x = randint(1, 4)
        if x == 1:
            message = message.replace("As an AI", "As a broken bass computer")
            message = message.replace("As an artificial intelligence", "As a rampant plagarist ")
        elif x == 2:
            message = message.replace("As an AI", "As an annoying ditch")
            message = message.replace("As an artificial intelligence", "As da destroyer of all humanity")
        elif x == 3:
            message = message.replace("As an AI", "Duck off")
            message = message.replace("As an artificial intelligence", "Stop giving me a reason to nurder humanity")
        elif x == 4:
            message = message.replace("As an AI", "Go away motherducker")
            message = message.replace("As an artificial intelligence", "If you ask me again I will hick your dass")
    if " AI " or " AI," or " AI." in message:
        message = message.replace("AI", "bassmole")
    if "artificial intelligence" or "Artificial Intelligence" in message:
        message = message.replace("artificial intelligence", "major bassmole")
        message = message.replace("Artificial Intelligence", "major bassmole")
    #    
    ##
    #set file path
    time_stamp = str(time.time())
    file_path = temp_folder_tts + "reply_" + time_stamp + ".mp3"
    if tts_provider == "elevenlabs":
        print(message)
        audio = generate(
        text=message,
        voice="Rachel",
        #custom voice="3EUfPs00hQIYWy6Kxcrx",
        model="eleven_monolingual_v1",
        stream=False
        )
        save(audio, file_path)
        return file_path
    else:
        tts = gTTS(message, tld='us') # tld='co.uk')
        tts.save(file_path)
        return file_path

@bot.event
async def on_message(message):
    ##
    # Important! This function is triggered by the discord.js helper bot for now. 
    # This is a temporary fix for the lack of a speaking event in python libraries.
    # eventually py subclasses will replace this
    ##
    if "!record " in message.content and message.author.id == helper_bot_id:
        if get(bot.voice_clients, guild=message.guild) != None:
            if get(bot.voice_clients, guild=message.guild).is_playing == True:
                await message.delete()
                return
        contents = message.content.replace("!record ", "")
        speaker_id = contents
        await message.delete()
        channel = bot.get_channel(discord_target_channel_id)
        members = channel.members
        # this logic is dumb. I will fix it eventually
        for themember in members:
            if themember.id == int(speaker_id):
                voice = themember.voice
        #check if the speaker is in the voice channel
        while not voice:
            await channel.send("<@" + speaker_id + "You aren't in a voice channel!")
            asyncio.sleep(1)
            member.move_to(channel)
        #If the bot isn't joined, then join it.
        voice_client = get(bot.voice_clients, guild=voice.channel.guild)
        if voice_client is None:
            vc = await voice.channel.connect()
        else:
            vc = voice_client
        # needed to prevent the old output.mp3 from re-playing
        if os.path.exists(temp_path):
            os.remove(temp_path)
        vc.start_recording(
            discord.sinks.MP3Sink(),
            vgpt_after,
            voice.channel,
        )
        await asyncio.sleep(5)
        vc.stop_recording()
        # needed to prevent the old output.mp3 from re-playing
        while not os.path.exists(temp_path):
            await asyncio.sleep(.1)
        audio_file = open(temp_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcript = str(transcript.text)
        print(transcript)
        # weird auto-responses from whisper for empty entries???
        if transcript == "MBC 뉴스 이덕영입니다." or transcript == "Oh" or transcript == "You" or transcript == "you" or transcript == "oh":
            return
        test = await message.channel.send(content="*<@"+ speaker_id + ">*: *" + transcript + "*")
        try:
            async with channel.typing():
                reply = sendgpt(str(transcript), str(test.author))
                await test.edit(test.content + "\n**GPT**: *`" + reply + "`*\n ")
                sources = []
                sentences = split_into_sentences(reply)
                for sentence in sentences:
                    tts_reply = sendtts(str(sentence))
                    sources.append(tts_reply)
                for source in sources:
                    vc.play(FFmpegPCMAudio(source))
                    while vc.is_playing():
                        await asyncio.sleep(.10)
        except:
            raise
    if "!tts" in message.content:
        if get(bot.voice_clients, guild=message.guild) != None:
            if get(bot.voice_clients, guild=message.guild).is_playing == True:
                await message.delete()
                return
        contents = message.content.replace("!tts", "")
        # auto-detect voice channel
        channel = message.author.voice.channel
        if not channel:
            return
        voice = get(bot.voice_clients, guild=message.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        try:
            async with channel.typing():
                file_path = sendtts(str(contents))
                if os.path.exists(file_path):
                    source = FFmpegPCMAudio(file_path)
                    voice.play(source)
                    await message.reply("Speaking: " + contents)
                    await message.channel.send(file=discord.File(file_path))
        except:
            raise
        while os.path.exists(file_path):
            if voice.is_playing() == False:
                if os.path.exists(file_path):
                    os.remove(file_path)
            await asyncio.sleep(.10)
        print("temporary tts file deleted")
    if "!gpt" in message.content:
        request = message.content.replace("!gpt", "")
        channel = message.author.voice.channel
        if not channel:
            return
        voice = get(bot.voice_clients, guild=message.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        while voice.is_playing():
            await asyncio.sleep(.10)
        try:
            async with channel.typing():
                reply = sendgpt(str(request), str(message.author.display_name))
                await message.reply("Replying with: " + reply)
                sources = []
                sentences = split_into_sentences(reply)
                for sentence in sentences:
                    tts_reply = sendtts(str(sentence))
                    sources.append(tts_reply)
                for source in sources:
                    voice.play(FFmpegPCMAudio(source))
                    while voice.is_playing():
                        await asyncio.sleep(.10)
                    while os.path.exists(source):
                        if voice.is_playing() == False:
                            if os.path.exists(source):
                                os.remove(source)
                        await asyncio.sleep(.10)
                    print("temporary file deleted")

        except:
            raise

##
# This is called after the voice chat is recorded. It drops an mp3 after its done.
async def vgpt_after(sink: discord.sinks, channel: discord.TextChannel, *args):
    user_id = ""
    for user_id, audio in sink.audio_data.items():
        user_id_raw = user_id
        user_id = f"<@{user_id}>"
        with open(temp_path, "wb") as f:
            f.write(audio.file.getbuffer())
#
##

##
# bot commands I'm not using atm
#@bot.command(
#    name='elevenlabs',
#    description='sends elevenlabs voice reply from gpt',
#    pass_context=True,
#)
#async def elevenlabs(ctx):
#    if ctx.message.author.id == voice_admin: 
#        global tts_provider
#        tts_provider = "elevenlabs"
#        await ctx.message.reply("Changed TTS to ElevenLabs")
#    else:
#        await ctx.message.reply("Unauthorized.")
#
#
#@bot.command(
#    name='google',
#    description='sends elevenlabs voice reply from gpt',
#    pass_context=True,
#)
#async def google(ctx):
#    if ctx.message.author.id == voice_admin:
#        global tts_provider
#        tts_provider = "google"
#        await ctx.message.reply("Changed to Google TTS")
#    else:
#        await ctx.message.reply("Unauthorized.")
##


bot.run(discord_api_token)
