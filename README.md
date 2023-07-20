# Discord Voice Bot
  Speak directly to GPT, search websites, get current weather, and more.  
  use push to talk.  
  GitHub: https://github.com/danomation  
  Patreon https://www.patreon.com/Wintermute310  
  
# Install Notes (ubuntu 22.04/debian):  
    sudo apt update && sudo apt upgrade  
    sudo apt install ffmpeg python3-pyaudio libportaudio2
    pip install -r requirements.txt     
    cd helper-bot    
    sudo apt install nodejs    
    sudo apt install npm    
    npm install discord.js    
    npm install @discordjs/voice    
The node.js requirement will be deprecated in future releases.  
Make 2 bots, add one for your helper-bot, and one for your bot.py bot  
Use this to help you create two bots using the discord developer portal  
https://discordpy.readthedocs.io/en/stable/discord.html  
sign up for openai, elevenlabs openweathermap and google search apis  
        
# Start:
    nohup python3 bot.py &    
    cd helper-bot    
    nohup npm start &    

# Demo (new feature: Trigger on voice):


https://github.com/danomation/GPT-4-Discord-Voice/assets/17872783/05b4932b-8db2-48c9-ba8c-4f42157e416a


# Todo:    
subclass the classes for the speaking event to remove node.js requirement  
Separate py files a bit to aid readability
