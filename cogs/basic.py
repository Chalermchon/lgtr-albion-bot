import os
import discord
from discord.ext import commands
import config


class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="ping", description="Check the connection.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Hi, {interaction.user.mention}!\nI'm ready for your command."
        )


async def setup(bot: commands.Bot):
    cog = os.path.basename(__file__)[:-3]
    guilds = []
    for guild_id, settings in config.GUILD_CONFIG.items():
        enabled_cogs = settings.get("enabled_cogs", [])
        if cog in enabled_cogs:
            guild = bot.get_guild(int(guild_id))
            guilds.append(guild)
            print(f"- Syncing '{cog}' cog for guild '{guild.name}' (ID: {guild.id}).")

    await bot.add_cog(Basic(bot), guilds=guilds)
    print(f"Loaded '{cog}' cog.")
