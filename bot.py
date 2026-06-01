import discord
import os
import aiohttp
import asyncio
import random
from flask import Flask
from threading import Thread

TOKEN = os.environ["TOKEN"]
HF_TOKEN = os.environ.get("HF_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Better fallback with variety
FALLBACK = [
    "I'm not sure, tell me more!",
    "Interesting! Go on.",
    "Hmm, let me think...",
    "Cool! 😎",
    "I'm listening.",
]

async def ai_reply(prompt):
    if not HF_TOKEN:
        return random.choice(FALLBACK)
    url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"max_length": 60, "temperature": 0.9}}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data[0].get("generated_text", "")
                    if reply.startswith(prompt):
                        reply = reply[len(prompt):].strip()
                    return reply[:150] if reply else random.choice(FALLBACK)
                return random.choice(FALLBACK)
    except:
        return random.choice(FALLBACK)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} AI bot ready")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "hello"
        async with message.channel.typing():
            reply = await ai_reply(prompt)
        await message.channel.send(f"{message.author.mention} {reply}")

# Keep-alive web server
app = Flask('')
@app.route('/')
def home(): return "QuantumX AI bot running"
@app.route('/health')
def health(): return "OK", 200
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run).start()

bot.run(TOKEN)
