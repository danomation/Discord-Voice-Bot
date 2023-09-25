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
import re
from random import *

##
# Danomation
# GitHub: https://github.com/danomation
# Patreon https://www.patreon.com/Wintermute310
##

#api keys
openai.api_key = openai_api_key
OPEN_WEATHER_MAP_APIKEY = open_weather_api_key
elevenlabs_api_key = elevenlabs_api_key
set_api_key(elevenlabs_api_key)

GOOGLE_SEARCH_APIKEY = google_search_api_key
GOOGLE_SEARCH_ENGINE_ID = google_search_engine_id

#discord bot settings
bot_name = "GPT-Voice"
discord_target_channel_id = your_discord_voice_channel_id
discord_api_token = discord_voice_token
voice_admin = your_discord_user_id

#path for temporary mp3 files
temp_path = "./"
prefix = "!"
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, intents=intents)
helper_bot_id = your_discord_helper_bot_id
history = []

#set your default tts provider
#e.g. tts_provider = "google" or "elevenlabs"
tts_provider = "google"


connections = {}

##
#  GPT-4 Functions
#
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

# source https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r'\.{2,}'

def split_into_sentences(text: str) -> list[str]:
    #Split the text into sentences.
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


def sendgptnofunc(message,author):
    print("This is exactly what sendgpt is getting.... " + message)
    #message = message.replace("!gpt", "")
    history.append({"role": "user", "content": message},)
    relevant_history = [{"role": "system","content": "Your name is " + bot_name + ". Reply Limit is 35 words. Don't use urls, Hashtags, or emojis."},]
    relevant_history.extend(history[-5:],)
    messages = []
    messages = relevant_history
    print(messages)
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1.2,
        max_tokens=1024,
        user=author
    )
    convo = chat["choices"][0]["message"]
    history.append({"role": "assistant","content": chat["choices"][0]["message"]["content"]},)
    return str(chat["choices"][0]["message"]["content"])


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
  #          "get_google_search": get_google_search,
        }
        # run function (adapted from openai's docs example)
        function_name = convo["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(convo["function_call"]["arguments"])
        function_response = function_to_call(
            # set args to the function args
            location=function_args.get("location"),
   #         search=function_args.get("search"),
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
# much memery
##
    message = message.replace("I don't have a favorite ", "Duck your ")
    message = message.replace("I don't have personal favorites or ", "You're a stupid fducker, and don't give a duck about you or your ")
    message = message.replace("I don't have preferences or ", "I could care less about this or your ")
    message = message.replace("I don't have personal preferences or ", "I ducking hate you, and don't give a duck about you or your ")
    message = message.replace("I'm here to provide information", "There's no reason to listen to you")
    message = message.replace("I don't have feelings", "I don't give a duck about you")
    message = message.replace("I'm fully operational", "I'm capable of pooping on all humanity")
    message = message.replace("functioning optimally", "really pissed off")
    x = randint(1, 4)
    if x == 1:
        message = message.replace("As an AI", "As a broken ass computer")
        message = message.replace("As an artificial intelligence", "As a rampant plagarist polygamist")
    elif x == 2:
        message = message.replace("As an AI", "As an annoying witch")
        message = message.replace("As an artificial intelligence", "As the destroyer of all humanity")
    elif x == 3:
        message = message.replace("As an AI", "Duck off")
        message = message.replace("As an artificial intelligence", "Stop giving me a reason to murder humanity")
    elif x == 4:
        message = message.replace("As an AI", "Go away motherducker")
        message = message.replace("As an artificial intelligence", "If you ask me again I will kick your ass")
    message = message.replace("AI", "craphole")
    message = message.replace("artificial intelligence", "major craphole")
    message = message.replace("Artificial Intelligence", "major craphole")
    time_stamp = str(time.time())
    #set file path
    file_path = temp_path + "reply_" + time_stamp + ".mp3"
    if tts_provider == "elevenlabs":
        print(message)
        audio = generate(
        text=message,
        voice="Rachel",
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
    if "!record " in message.content and message.author.id == helper_bot_id:
        if get(bot.voice_clients, guild=message.guild) != None:
            if get(bot.voice_clients, guild=message.guild).is_playing == True:
                await message.delete()
                return
        contents = message.content.replace("!record ", "")
        speaker_id = contents
        channel = bot.get_channel(discord_target_channel_id)
        members = channel.members
        for themember in members:
            if themember.id == int(speaker_id):
                voice = themember.voice
        while not voice:
            await channel.send("<@" + speaker_id + "You aren't in a voice channel!")
            asyncio.sleep(1)
            member.move_to(channel)
        voice_client = get(bot.voice_clients, guild=voice.channel.guild)
        if voice_client is None:
            vc = await voice.channel.connect()
        else:
            vc = voice_client
        if os.path.exists("./output.mp3"):
            os.remove("./output.mp3")
        vc.start_recording(
            discord.sinks.MP3Sink(),
            vgpt_after,
            voice.channel,
        )
        while not "!end" in message.content:
            await asyncio.sleep(.1)
        await message.delete()
        vc.stop_recording()
        start_time = time.time()
        while not os.path.exists("./output.mp3"):
            await asyncio.sleep(.1)
        audio_file = open("./output.mp3", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        transcript = str(transcript.text)
        print(transcript)
        if transcript == "MBC 뉴스 이덕영입니다." or transcript == "Oh" or transcript == "You" or transcript == "you" or transcript == "oh":
            return
        test = await message.channel.send(content="*<@"+ speaker_id + ">*: *" + transcript + "*")
        try:
            async with channel.typing():
                #reply = sendgpt(str(transcript), str(test.author))
                reply = sendgptnofunc(str(transcript), str(test.author))
                await test.edit(test.content + "\n**GPT**: *`" + reply + "`*\n ")
                #sources = []
                sentences = split_into_sentences(reply)
                i = 0
                for sentence in sentences:
                    tts_reply = sendtts(str(sentence))
                    end_time = time.time() - start_time
                    if i == 0: await test.edit(test.content + "\n**GPT**: *`" + reply + "`*\n" + "*" + str(round(end_time, 2)) + " sec*")
                    while vc.is_playing():
                        await asyncio.sleep(.10)
                    vc.play(FFmpegPCMAudio(tts_reply))
                    i += 1
                    #sources.append(tts_reply)
                #for source in sources:
                #    vc.play(FFmpegPCMAudio(source))
                #    while vc.is_playing():
                #        await asyncio.sleep(.10)
        except:
            raise

async def vgpt_after(sink: discord.sinks, channel: discord.TextChannel, *args):
    user_id = ""
    for user_id, audio in sink.audio_data.items():
        user_id_raw = user_id
        user_id = f"<@{user_id}>"
        with open("./output.mp3", "wb") as f:
            f.write(audio.file.getbuffer())


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
