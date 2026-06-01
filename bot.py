import discord
import os
import aiohttp
import asyncio
import random
from flask import Flask
from threading import Thread

# ============================================
# Environment Variables
# ============================================
TOKEN = os.environ["TOKEN"]
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# ============================================
# Discord Bot Setup
# ============================================
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Fallback responses (used only if AI fails)
FALLBACK = [
    "That's interesting! Tell me more.",
    "I see. What else is on your mind?",
    "Hmm, let me think...",
    "Cool! 😎",
    "I'm listening.",
]

# ============================================
# AI Function with Logging
# ============================================
async def get_ai_reply(msg):
    """Call Hugging Face free conversational AI with detailed logging."""
    if not HF_TOKEN or HF_TOKEN == "":
        print("❌ No HF_TOKEN found in environment.")
        return random.choice(FALLBACK)
    
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
        print(f"🤖 Sending to AI: {msg}")
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"📡 AI responded with status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"📦 AI raw response: {data}")
                    if isinstance(data, list) and len(data) > 0:
                        reply = data[0].get("generated_text", "")
                        if reply.startswith(msg):
                            reply = reply[len(msg):].strip()
                        if reply:
                            print(f"✅ AI reply: {reply}")
                            return reply[:200]
                else:
                    text = await resp.text()
                    print(f"⚠️ AI error {resp.status}: {text}")
                return random.choice(FALLBACK)
    except asyncio.TimeoutError:
        print("⏰ AI request timed out after 15 seconds.")
        return random.choice(FALLBACK)
    except Exception as e:
        print(f"💥 AI exception: {type(e).__name__} - {e}")
        return random.choice(FALLBACK)

# ============================================
# Discord Event Handlers
# ============================================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with REAL AI replies!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "hello"
        print(f"📩 Mention received: '{prompt}' from {message.author}")
        
        async with message.channel.typing():
            reply = await get_ai_reply(prompt)
        
        print(f"💬 Sending reply: {reply}")
        await message.channel.send(f"{message.author.mention} {reply}")

# ============================================
# Flask Keep-Alive Server (MUST be before bot.run)
# ============================================
app = Flask('')

@app.route('/')
def home():
    return "QuantumX Bot is alive with AI!"

@app.route('/health')
def health():
    return "OK", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

Thread(target=run_web).start()

# ============================================
# Start Discord Bot
# ============================================
bot.run(TOKEN)
