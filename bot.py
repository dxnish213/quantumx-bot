import discord
import os
import aiohttp
import asyncio
from flask import Flask
from threading import Thread

TOKEN = os.environ["TOKEN"]
HF_TOKEN = os.environ.get("HF_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

async def test_ai(prompt):
    """Test AI and return reply or error message."""
    if not HF_TOKEN:
        return "❌ No HF_TOKEN found. Add it in Render Environment."
    
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
                    return reply if reply else "🤖 (no response)"
                else:
                    text = await resp.text()
                    return f"⚠️ API error {resp.status}: {text[:100]}"
    except asyncio.TimeoutError:
        return "⏰ AI timeout (free tier slow). Try again."
    except Exception as e:
        return f"💥 Exception: {type(e).__name__}"

@bot.event
async def on_ready():
    print(f"✅ Bot ready: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "hello"
        async with message.channel.typing():
            reply = await test_ai(prompt)
        await message.channel.send(f"{message.author.mention} {reply}")

# Keep-alive
app = Flask('')
@app.route('/')
def home(): return "OK"
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run).start()

bot.run(TOKEN)
