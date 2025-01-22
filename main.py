import discord
from discord.ext import commands
import config
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)


# Dynamically load all cogs
def load_cogs():
    execute_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.join(execute_dir, "cogs")

    cogs = []
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            cogs.append(filename[:-3])
    return cogs


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Bot is ready!")

    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()

    cogs = load_cogs()

    for cog in cogs:
        try:
            print(f"Loading {cog} cog...")
            await bot.load_extension(f"cogs.{cog}")

        except Exception as e:
            print(f"Failed to load {cog} cog: {e}")

    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)


# Run the bot
async def main():
    async with bot:
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
