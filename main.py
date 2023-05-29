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
        self._cd = commands.CooldownMapping.from_cooldown(1, 10.0, commands.BucketType.member)

    async def setup_hook(self) -> None:
        for ext in self.cogs_list:
            await self.load_extension(ext)

    @staticmethod
    async def on_ready():
        print(f'Ready {client.user}')
        try:
            synced = await client.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    def get_ratelimit(self, message: discord.Message):
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

    async def on_message(self, message):
        if message.content == "meow" and message.author.id != client.user.id:
            ratelimit = self.get_ratelimit(message)
            if ratelimit is None:
                await message.reply("meow")

    '''@app_commands.command(name="stop_commands", description="Stop all currently running commands")
    async def stop(self, interaction: discord.Interaction):
        
        await interaction.response.send_message("Execution stopped (not implemented)", ephemeral=True)'''


with open("config.json", "r") as f:
    data = json.load(f)
    TOKEN = data["TOKEN"]
    FLAPJACK = data["FLAPJACK"]
client = Client()
client.run(TOKEN)
