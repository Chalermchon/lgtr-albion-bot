import os
from dotenv import load_dotenv
import discord
from discord import app_commands
import networkx as nx

load_dotenv()

graph = nx.DiGraph()

MY_GUILD = discord.Object(id=985210349915615283)  # replace with your guild id


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.clear_commands(guild=MY_GUILD)
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command()
async def ping(interaction: discord.Interaction):
    """Check the connection."""
    await interaction.response.send_message(f'''Hi, {interaction.user.mention}. I'm running''')

@client.tree.command()
@app_commands.describe(
    first_map="ex: Dusktree Swamp, Qiient-Nutis",
    second_map="ex: Dusktree Swamp, Qiient-Nutis"
)
async def path(interaction: discord.Interaction, first_map: str, second_map: str):
    graph.add_edge(first_map, second_map)
    graph.add_edge(second_map, first_map)
    await interaction.response.send_message(f"Set path '{first_map}' <> '{second_map}' successfully.")

@client.tree.command()
@app_commands.describe(
    from_map="ex: Dusktree Swamp, Qiient-Nutis",
    to_map="ex: Dusktree Swamp, Qiient-Nutis"
)
async def route(interaction: discord.Interaction, from_map: str, to_map: str):
    try:
        shortest_path = nx.shortest_path(graph, source=from_map, target=to_map)
        shortest_path = " -> ".join(shortest_path)
        await interaction.response.send_message(f"Path from '{from_map}' to '{to_map}':\n{shortest_path}")
    except nx.NodeNotFound as e:
        missing_map = str(e).split(" ", 1)[1].replace("is not in G", "").strip()
        await interaction.response.send_message(f'{missing_map} is not set')
    except nx.NetworkXNoPath as e:
        await interaction.response.send_message(str(e))


client.run(os.getenv('DISCORD_BOT_TOKEN'))