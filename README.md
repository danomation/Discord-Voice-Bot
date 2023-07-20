# Discord Voice Bot
  Speak directly to GPT, adds external websites, weather, and more.  
  use push to talk.  
  GitHub: https://github.com/danomation  
  Patreon https://www.patreon.com/Wintermute310  
  
# Install Notes
(update: temporarily you will need node.js, discord.js v13, and @discordjs/voice also)  
make 2 bots, add one for your helper-bot, and one for your bot.py bot    
https://discordpy.readthedocs.io/en/stable/discord.html     
ubuntu 22.04/debian:  
        sudo apt update && sudo apt upgrade  
        pip install -r requirements.txt    
        sudo apt install ffmpeg    
        sudo apt-get install libportaudio2  
        sudo apt-get install python3-pyaudio       
        mkdir helper-bot    
        cd helper-bot    
        sudo apt install nodejs    
        sudo apt install npm    
        npm install discord.js    
        npm install @discordjs/voice    
        
# Start bots
    nohup python3 bot.py &    
    cd helper-bot    
    nohup npm start &    ss

# Demo (new feature: Trigger on voice)


https://github.com/danomation/GPT-4-Discord-Voice/assets/17872783/05b4932b-8db2-48c9-ba8c-4f42157e416a


# Todo:    
subclass the classes for the speaking event to remove node.js requirement  
Separate py files a bit to aid readability
