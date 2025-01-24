import os
import asyncio
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands
import config
from albion.maps import (
    get_maps,
    add_roa_portal,
    get_displayname,
    get_route,
    get_roa_portal_closing_datetime,
)
from albion.maps.exceptions import NoRoute, MapNotFound


class RoadOfAva(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def map_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[discord.app_commands.Choice[str]]:
        start_with_keyword = []
        contain_keyword = []
        for id, displayname in get_maps().items():
            displayname_without_symbol = " ".join(displayname.split(" ")[1:])
            if len(start_with_keyword + contain_keyword) == 15:
                break
            if displayname_without_symbol.lower().startswith(current.lower()):
                start_with_keyword.append(
                    discord.app_commands.Choice(name=displayname, value=id)
                )
            if displayname_without_symbol not in start_with_keyword and current.lower() in displayname_without_symbol.lower():
                contain_keyword.append(
                    discord.app_commands.Choice(name=displayname, value=id)
                )

        return (start_with_keyword + contain_keyword)[:15]

    @discord.app_commands.command(
        name="portal", description="Insert a new Road of Avalon portal."
    )
    @discord.app_commands.describe(
        from_map="Current map.",
        to_map="Destination map.",
        duration="The closing time of portal (ex: 1h23m45s, 1m23s, 12s).",
    )
    @discord.app_commands.autocomplete(
        from_map=map_autocomplete,
        to_map=map_autocomplete,
    )
    async def portal(
        self,
        interaction: discord.Interaction,
        from_map: str,
        to_map: str,
        duration: str,
    ):
        closing_datetime = add_roa_portal(from_map, to_map, duration)

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"Portal between {get_displayname(from_map)} and {get_displayname(to_map)}",
                description=f"Close around {closing_datetime.strftime('%d %b, %H:%M:%S')} (UTC+7).",
                colour=discord.Colour.green(),
            )
        )
        timer = (
            closing_datetime - datetime.now(timezone(timedelta(hours=7)))
        ).total_seconds()

        async def edit_message_when_almost_close():
            EDIT_WHEN_TIME_LEFT_SECOND = 30 * 60  # 30 mins
            await asyncio.sleep(timer - EDIT_WHEN_TIME_LEFT_SECOND)
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title=f"Portal between `{get_displayname(from_map)}` and `{get_displayname(to_map)}`",
                    description=f"Close around {closing_datetime.strftime('%d %b, %H:%M:%S')} (UTC+7).",
                    colour=discord.Colour.yellow(),
                )
            )

        async def remove_message_when_already_closed():
            await asyncio.sleep(timer)
            await interaction.delete_original_response()

        asyncio.ensure_future(edit_message_when_almost_close())
        asyncio.ensure_future(remove_message_when_already_closed())

    @discord.app_commands.command(name="route", description="Get route between maps.")
    @discord.app_commands.describe(
        from_map="Source Map.",
        to_map="Target Map.",
    )
    @discord.app_commands.autocomplete(
        from_map=map_autocomplete,
        to_map=map_autocomplete,
    )
    async def route(self, interaction: discord.Interaction, from_map: str, to_map: str):
        try:
            map_ids = get_route(from_map, to_map)
            description = ""
            nearly_closed_datetime: datetime = None
            for index, map_id in enumerate(map_ids):
                description += f">> **`{get_displayname(map_id)}`**"
                if index != 0:
                    closing_datetime = get_roa_portal_closing_datetime(
                        map_id_a=map_ids[index - 1], map_id_b=map_id
                    )
                    if closing_datetime:
                        description += f"\n*close around {closing_datetime.strftime('%d %b, %H:%M:%S')} (UTC+7)*"
                        if (
                            nearly_closed_datetime == None
                            or closing_datetime < nearly_closed_datetime
                        ):
                            nearly_closed_datetime = closing_datetime
                description += "\n"

            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"Route from `{get_displayname(from_map)}` to `{get_displayname(to_map)}`.",
                    description=description,
                    color=discord.Colour.blue(),
                )
            )

            if nearly_closed_datetime:

                async def remove_message_when_already_closed():
                    await asyncio.sleep(
                        (
                            closing_datetime
                            - datetime.now(timezone(timedelta(hours=7)))
                        ).total_seconds()
                    )
                    await interaction.delete_original_response()

                asyncio.ensure_future(remove_message_when_already_closed())

        except (MapNotFound, NoRoute) as e:
            if isinstance(e, MapNotFound):
                missing_map = e
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"`{get_displayname(missing_map)}` was not set.",
                        colour=discord.Colour.red(),
                    )
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"No route from `{get_displayname(from_map)}` to `{get_displayname(to_map)}`.",
                        colour=discord.Colour.red(),
                    )
                )

            async def remove_message_when_already_closed():
                await asyncio.sleep(10)
                await interaction.delete_original_response()

            asyncio.ensure_future(remove_message_when_already_closed())


async def setup(bot: commands.Bot):
    cog = os.path.basename(__file__)[:-3]
    guilds = []
    for guild_id, settings in config.GUILD_CONFIG.items():
        enabled_cogs = settings.get("enabled_cogs", [])
        if cog in enabled_cogs:
            guild = bot.get_guild(int(guild_id))
            guilds.append(guild)
            print(f"- Syncing '{cog}' cog for guild '{guild.name}' (ID: {guild.id}).")

    await bot.add_cog(RoadOfAva(bot), guilds=guilds)
    print(f"Loaded '{cog}' cog.")
