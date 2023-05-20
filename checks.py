import discord
from discord.ext import commands
import json


def _channels() -> dict[str, int]:
    with open('overwatch.json', 'r') as f:
        return json.load(f)


def valid_channel():
    def predicate(ctx):
        return _channels().get(str(ctx.guild.id)) == ctx.channel.id
    return commands.check(predicate)
