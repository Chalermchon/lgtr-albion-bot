import os
from dotenv import load_dotenv
import json

config_dir = os.path.dirname(os.path.abspath(__file__))


def load_guild_config():
    try:
        config_path = os.path.join(config_dir, "guild_config.json")

        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: guild_config.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from guild_config.json.")
        return {}


# Load variables from .env
load_dotenv()

# Access variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PREFIX = os.getenv("PREFIX", "!")
GUILD_CONFIG = load_guild_config()
