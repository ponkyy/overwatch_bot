import discord
from discord.ext import commands
from random import randint
from time import sleep


class Game:

    def __init__(self, _id):
        self.id = _id
        self.board = Board()
        self.move_count = 0
        self.win = False




class Board:

    def __init__(self):
        self.board = [f"[{str(x)}]" if x != 9 else "[*]" for x in range(1, 10)]


class Tilegame(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.games = {}
        # self.games = {<guild id>: Game()}

    @commands.command()
    async def tilegame(self, ctx, operation):
        mode = getattr(self, operation)
        msg = mode(ctx.guild.id)
        await ctx.send(msg)

    def start(self, guild_id):
        if guild_id in self.games:
            return "No"
        self.games[guild_id] = Game(guild_id)

        return "Done"



    def quit(self, guild_id):
        pass


async def setup(client):
    await client.add_cog(Tilegame(client))
