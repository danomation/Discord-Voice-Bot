import { Client, GatewayIntentBits, Events } from 'discord.js';
import { joinVoiceChannel, SpeakingMap} from '@discordjs/voice';
import { writeFileSync } from 'fs';
import pkg from '@discordjs/opus';
const { OpusEncoder } = pkg;

// set these:
// your voice channel
const voice_channel_id = ''
// your bot.py bot id
const bot_py_id = ''
// your discord token
const discord_token = ''

// not used
//  Maps userIds to their speaking states.
//const speakingStates = new Map();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds, // These are the permissions the bot has
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
    const myuser = Array.from(connection.receiver.speaking.users.keys())[0];
    // ironically this is the trigger for the main bot right now. I know it's hacky as heck.
    if (myuser != bot_py_id) channel.send("!record "+ myuser);
    console.log(myuser + " started speaking");

    //const mytest = Array.from(connection.receiver.speaking.users.keys());
    //mytest.forEach(element => {
    //  speakingStates.set(element, true);
    //});
    //console.log(speakingStates);
  });

// didn't need it
//  connection.receiver.speaking.on('end', async() => {
//    const myuser = Array.from(connection.receiver.speaking.users.keys())[0];
//    console.log(myuser + " stopped speaking");
//    const mytest = Array.from(connection.receiver.speaking.users.keys());
//    mytest.forEach(element => {
//      speakingStates.set(element, false);
//    });
//    console.log(speakingStates);
//  });


//  speakingMap.on('start', (userId) => {
//    speakingStates.set(myuser, true);
//    writeFileSync('speakingStatus.json', JSON.stringify(Array.from(speakingStates.entries()), null, 2));
//  });

//  speakingMap.on('end', (userId) => {
//    speakingStates.set(userId, false);
//    writeFileSync('speakingStatus.json', JSON.stringify(Array.from(speakingStates.entries()), null, 2));
//  });

});


client.login(discord_token);
