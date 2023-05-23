import discord
from discord import app_commands
from discord.ext import commands
import json


class Client(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(".."),
            intents=discord.Intents().all()
        )
        self.cogs_list = ["cogs.overwatch2"]

    async def setup_hook(self) -> None:
        for ext in self.cogs_list:
            await self.load_extension(ext)

    async def on_ready(self):
        print(f'Ready {client.user}')
        try:
            synced = await client.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)


with open("config.json", "r") as f:
    data = json.load(f)
    TOKEN = data["TOKEN"]
client = Client()
client.run(TOKEN)
