import discord
import os
import aiohttp
import asyncio
from flask import Flask
from threading import Thread

TOKEN = os.environ["TOKEN"]
ONE_MIN_AI_KEY = os.environ.get("ONE_MIN_AI_KEY", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

async def ai_reply(prompt):
    if not ONE_MIN_AI_KEY:
        return "❌ ONE_MIN_AI_KEY missing. Add it in Render Environment."
    
    url = "https://api.1min.ai/text"
    headers = {
        "Authorization": f"Bearer {ONE_MIN_AI_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    return reply[:200] if reply else "🤖 No response from AI."
                else:
                    return f"⚠️ API error {resp.status}. Try again."
    except asyncio.TimeoutError:
        return "⏰ AI timeout. Try again."
    except Exception as e:
        return f"💥 Error: {type(e).__name__}"

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with 1min.ai!")

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

# Keep-alive server
app = Flask('')
@app.route('/')
def home(): return "QuantumX Bot online"
@app.route('/health')
def health(): return "OK", 200
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run).start()

bot.run(TOKEN)
