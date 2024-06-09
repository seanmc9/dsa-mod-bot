import discord, os
from dotenv import load_dotenv

load_dotenv() # so we can easily access env vars
TOKEN = os.getenv("TOKEN")

client = discord.Client()

# EVENTS

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await message.channel.send("Hello!")

client.run(TOKEN)