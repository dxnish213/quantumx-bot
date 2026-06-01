import discord
import os
import aiohttp
import asyncio
import json
from flask import Flask
from threading import Thread

TOKEN = os.environ["TOKEN"]
ONE_MIN_AI_KEY = os.environ.get("ONE_MIN_AI_KEY", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Global variable to store the conversation ID for context
conversation_id = None

async def ai_reply(prompt):
    global conversation_id
    if not ONE_MIN_AI_KEY:
        return "❌ ONE_MIN_AI_KEY missing. Add it in Render Environment."

    # API headers require 'API-KEY' (not 'Authorization: Bearer')
    headers = {
        "API-KEY": ONE_MIN_AI_KEY, # <-- Changed from 'Authorization'
        "Content-Type": "application/json"
    }

    # 1. Create a conversation if we don't have an ID yet
    if conversation_id is None:
        create_payload = {
            "type": "CHAT_WITH_AI",
            "title": "Discord Bot Session",
            "model": "gpt-4o-mini"  # You can change this to 'gpt-4o', 'claude-3-haiku', etc.
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.1min.ai/api/conversations", headers=headers, json=create_payload, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        conversation_id = data.get('conversation', {}).get('uuid')
                        if not conversation_id:
                            return "🤖 Could not start a new conversation. Please try again."
                    else:
                        return f"⚠️ Failed to create conversation (Status: {resp.status}). Please check your API key."
        except asyncio.TimeoutError:
            return "⏰ Request to create conversation timed out."
        except Exception as e:
            return f"💥 Conversation creation error: {type(e).__name__}"

    # 2. Send the user's prompt to the conversation
    send_payload = {
        "type": "CHAT_WITH_AI",
        "model": "gpt-4o-mini",
        "conversationId": conversation_id,
        "promptObject": {"prompt": prompt}
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.1min.ai/api/features", headers=headers, json=send_payload, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Extract the reply text from the correct path in the JSON
                    reply = data.get('aiRecord', {}).get('aiRecordDetail', {}).get('resultObject', [None])[0]
                    # Clean up the reply
                    return reply[:200] if reply else "🤖 No response from AI."
                else:
                    return f"⚠️ AI request failed (Status: {resp.status}). Try again."
    except asyncio.TimeoutError:
        return "⏰ AI request timed out after 20 seconds. Try again."
    except Exception as e:
        return f"💥 Error: {type(e).__name__}"

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with the corrected 1min.ai API!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        # Remove the mention from the prompt
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "Hello! Who are you?"
        
        async with message.channel.typing():
            reply = await ai_reply(prompt)
        
        await message.channel.send(f"{message.author.mention} {reply}")

# Keep-alive web server
app = Flask('')
@app.route('/')
def home(): return "QuantumX Bot online"
@app.route('/health')
def health(): return "OK", 200
def run(): app.run(host='0.0.0.0', port=10000)
Thread(target=run).start()

bot.run(TOKEN)
