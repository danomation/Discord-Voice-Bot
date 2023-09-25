import { Client, GatewayIntentBits, Events } from 'discord.js';
import { joinVoiceChannel, SpeakingMap} from '@discordjs/voice';
import { writeFileSync } from 'fs';
import pkg from '@discordjs/opus';
const { OpusEncoder } = pkg;
const speakingStates = new Map();

// set these:
// your voice channel
const voice_channel_id = ''
// your bot.py bot id
const bot_py_id = ''
// your discord token
const discord_token = ''

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
  ],
});


client.once('ready', async () => {
  const channel = client.channels.resolve(voice_channel_id);
  if (!channel) return console.error("The channel was not found!");
  const connection = joinVoiceChannel({
    channelId: channel.id,
    guildId: channel.guild.id,
    adapterCreator: channel.guild.voiceAdapterCreator,
  });

  connection.receiver.speaking.on('start', async() => {
    var speakinguser = Array.from(connection.receiver.speaking.users.keys())[0];
    if (speakinguser != bot_py_id){
        global.myuser = speakinguser;
        global.mymessage = await channel.send("!record "+ myuser);
        console.log(global.myuser + " started speaking");
    }
  });

  connection.receiver.speaking.on('end', async() => {
    var speakinguser = Array.from(connection.receiver.speaking.users.keys())[0];
    if (speakinguser != bot_py_id){
        const theuser = Array.from(connection.receiver.speaking.users.keys())[0];
        if (myuser == global.myuser) global.mymessage.edit(mymessage.content + " !end")
        console.log(myuser + " stopped speaking");
    }
  });

});


client.login(discord_token);
