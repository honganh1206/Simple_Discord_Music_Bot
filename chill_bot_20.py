from dotenv import load_dotenv
from discord.ext import commands
from music import MusicBot
import discord
import os

load_dotenv()

# allow bot to subscribe to specific buckets/ALL events (include presences and members)

intents = discord.Intents().all()
bot = commands.Bot(command_prefix=commands.when_mentioned_or("$"), intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is here! (ID: {bot.user.id})')
    print('-' *5)


TOKEN = os.getenv('BOT_TOKEN')
bot.add_cog(MusicBot(bot))
bot.run(TOKEN)
