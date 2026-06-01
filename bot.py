import discord
import os
import aiohttp
import asyncio
import socket
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

# ============================================
# Test DNS on startup (logs to console)
# ============================================
try:
    socket.gethostbyname('api-inference.huggingface.co')
    print("✅ DNS resolved successfully")
except:
    print("❌ DNS resolution failed – will use fallback endpoints")

# ============================================
# AI Function with Multiple Endpoint Fallbacks
# ============================================
async def ai_reply(prompt):
    if not HF_TOKEN:
        return "❌ No HF_TOKEN found. Please add it in Render Environment."

    # List of free conversational models (try each until one works)
    endpoints = [
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small",
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
    ]
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 80,
            "temperature": 0.9,
            "top_p": 0.9,
            "do_sample": True
        }
    }

    for url in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            reply = data[0].get("generated_text", "")
                            if reply.startswith(prompt):
                                reply = reply[len(prompt):].strip()
                            if reply:
                                return reply[:200]
                    elif resp.status == 503:
                        # Model is loading – wait a bit and try next endpoint
                        await asyncio.sleep(1)
                        continue
                    else:
                        # Other error – print for logs, try next endpoint
                        text = await resp.text()
                        print(f"API error {resp.status} on {url}: {text[:100]}")
                        continue
        except asyncio.TimeoutError:
            print(f"Timeout on {url}")
            continue
        except Exception as e:
            print(f"Exception on {url}: {type(e).__name__}")
            continue

    # If all endpoints fail
    return "🤖 AI is currently unavailable (free tier limits). Please try again in a minute."

# ============================================
# Discord Event Handlers
# ============================================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with AI!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Respond when the bot is @mentioned
    if bot.user in message.mentions:
        # Remove the mention from the prompt
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "hello"
        
        # Show typing indicator while AI thinks
        async with message.channel.typing():
            reply = await ai_reply(prompt)
        
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

# Start the web server in a background thread
Thread(target=run_web).start()

# ============================================
# Start Discord Bot
# ============================================
bot.run(TOKEN)
