import discord
import os
import aiohttp
import asyncio
import random

TOKEN = os.environ["TOKEN"]
HF_TOKEN = os.environ.get("HF_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Fallback responses only if AI fails
FALLBACK = [
    "That's interesting! Tell me more.",
    "I see. What else is on your mind?",
    "Hmm, let me think...",
    "Cool! 😎",
    "I'm listening.",
]

async def get_ai_reply(msg):
    """Call Hugging Face free conversational AI."""
    if not HF_TOKEN or HF_TOKEN == "":
        return random.choice(FALLBACK)
    
    # Use a small, fast model
    API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": msg,
        "parameters": {
            "max_length": 80,
            "temperature": 0.9,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        reply = data[0].get("generated_text", "")
                        # Remove the original prompt if repeated
                        if reply.startswith(msg):
                            reply = reply[len(msg):].strip()
                        if reply:
                            return reply[:200]
                # If API fails, fallback
                return random.choice(FALLBACK)
    except Exception as e:
        print(f"AI error: {e}")
        return random.choice(FALLBACK)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with REAL AI replies!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Respond when bot is @mentioned
    if bot.user in message.mentions:
        # Remove the mention from the prompt
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "hello"
        
        # Show typing indicator while AI thinks
        async with message.channel.typing():
            reply = await get_ai_reply(prompt)
        
        await message.channel.send(f"{message.author.mention} {reply}")

# === Flask keep-alive server (must be BEFORE bot.run) ===
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "QuantumX Bot is alive with AI!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

Thread(target=run_web).start()

# === Start Discord bot ===
bot.run(TOKEN)
