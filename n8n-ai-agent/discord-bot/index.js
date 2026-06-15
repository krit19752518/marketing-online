require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');

// Create a new client instance
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// When the client is ready, run this code (only once)
client.once('ready', () => {
  console.log(`Ready! Logged in as ${client.user.tag}`);
});

// Login to Discord with your client's token
client.login(process.env.DISCORD_TOKEN);
