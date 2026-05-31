import discord
import os

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await message.channel.send(f"{message.author.display_name} said: {message.content}")

bot.run(TOKEN)
