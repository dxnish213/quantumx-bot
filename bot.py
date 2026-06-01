import discord
import os
import aiohttp
import asyncio
from flask import Flask
from threading import Thread

TOKEN = os.environ["TOKEN"]
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

async def ai_reply(prompt):
    if not GEMINI_KEY:
        return "❌ GEMINI_KEY missing. Add it in Render Environment."
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    return reply[:200] if reply else "🤖 No response."
                else:
                    text = await resp.text()
                    return f"⚠️ API error {resp.status}: {text[:100]}"
    except asyncio.TimeoutError:
        return "⏰ AI timeout. Try again."
    except Exception as e:
        return f"💥 Error: {type(e).__name__}"

@bot.event
async def on_ready():
    print(f"✅ {bot.user} online with Gemini AI!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "Hello!"
        async with message.channel.typing():
            reply = await ai_reply(prompt)
        await message.channel.send(f"{message.author.mention} {reply}")

# Keep-alive server
app = Flask('')
@app.route('/')
def home(): return "QuantumX Bot online"
@app.route('/health')
def health(): return "OK", 200
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run).start()

bot.run(TOKEN)
