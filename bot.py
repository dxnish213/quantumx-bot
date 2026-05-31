import discord
import o
import requests
import random

TOKEN = os.environ["TOKEN"]
HF_TOKEN = os.environ.get("HF_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

FALLBACK = [
    "That's cool! Tell me more.",
    "I see. What else?",
    "Interesting!",
    "Hmm, go on.",
    "I'm listening!",
]

def get_ai_reply(msg):
    if not HF_TOKEN or HF_TOKEN == "":
        return random.choice(FALLBACK)
    API = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": msg, "parameters": {"max_length": 100, "temperature": 0.7}}
    try:
        r = requests.post(API, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                reply = data[0].get("generated_text", "")
                if reply.startswith(msg):
                    reply = reply[len(msg):].strip()
                if reply:
                    return reply[:200]
        return random.choice(FALLBACK)
    except:
        return random.choice(FALLBACK)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with AI brain!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "hello"
        async with message.channel.typing():
            reply = get_ai_reply(prompt)
        await message.channel.send(f"{message.author.mention} {reply}")

bot.run(TOKEN)
