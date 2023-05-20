import asyncio

import discord
import os
import json
from discord.ext import commands
import random

intents = discord.Intents.all()
client = commands.Bot(command_prefix="..", intents=intents)


@client.event
async def on_ready():
    print(f'Ready {client.user}')


@client.event
async def on_guild_join(guild):
    with open('words.json', 'r') as f:
        words = json.load(f)
    words[str(guild.id)] = {}

    with open('words.json', 'w') as f:
        json.dump(words, f, indent=4)


@client.event
async def on_guild_remove(guild):
    with open('words.json', 'r') as f:
        words = json.load(f)
    words.pop(str(guild.id))

    with open('words.json', 'w') as f:
        json.dump(words, f, indent=4)


@client.command()
async def add_word(ctx, word, *args):
    if not args:
        await ctx.send("I need a message to respond with.")
        return
    with open('words.json', 'r') as f:
        words = json.load(f)
    curr = words[str(ctx.guild.id)]
    if word in curr:
        await ctx.send(f"{word=} is already added.")
        return
    curr[word] = " ".join(args)

    with open('words.json', 'w') as f:
        json.dump(words, f, indent=4)


@client.command()
async def remove_word(ctx, word):
    with open('words.json', 'r') as f:
        words = json.load(f)
    curr = words[str(ctx.guild.id)]
    if word not in curr:
        await ctx.send(f"{word=} has not been added.")
        return
    curr.pop(word)

    with open('words.json', 'w') as f:
        json.dump(words, f, indent=4)


@client.command(hidden=True)
async def show_words(ctx):
    with open('words.json', 'r') as f:
        await ctx.send(json.load(f)[str(ctx.guild.id)])


@client.command()
async def del_words(ctx):
    with open('words.json', 'r') as f:
        words = json.load(f)
    words[str(ctx.guild.id)] = {}

    with open('words.json', 'w') as f:
        json.dump(words, f, indent=4)


'''@client.command(hidden=True)
async def show_guilds(ctx):
    print(ctx.send(str(client.guilds)))'''


'''@client.command(hidden=True)
async def show_channels(ctx, guild_id):
    for guild in client.guilds:
        if guild.id == int(guild_id):
            for channel in guild.channels:
                print(f"name: {channel.name}, id: {channel.id}, type: {channel.type}")
            print()
'''

'''@client.command(hidden=True)
async def announce(ctx, message):
    for guild in client.guilds:
        if guild == ctx.guild:
            pass'''


'''@client.command(hidden=True)
async def show_message_history(ctx):
    async for msg in ctx.channel.history(limit=5):
        print(msg.content)'''


@client.event
async def on_message(msg):

    '''if not msg.author == client.user:
        print(
            f"From \"{msg.guild.name}\" in #{msg.channel.name}: {msg.content}"
        )'''
    # scan for word
    with open('words.json', 'r') as f:
        words = json.load(f)
    _id = str(msg.guild.id)
    if msg.author != client.user and msg.content in words[_id]:
        await msg.channel.send(f"{words[_id][msg.content]}")

    # meow
    '''if msg.content == "meow" and msg.author != client.user:
        await msg.channel.send("meow")

    '''

    # flapjacks image

    ponky = 285164262555648000
    flapjacks = 746146914634039438

    if msg.author.id == ponky:
        r = random.randint(1, 100000)
        if r == 500:
            await msg.channel.send(file=discord.File('heisenduck.png'))

    if msg.author.id == flapjacks:
        r = random.randint(1, 100000)
        if r == 500:
            await msg.channel.send(file=discord.File('flapjacks.gif'))

    await client.process_commands(msg)


async def load_extensions():
    for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            await client.load_extension(f'cogs.{file[:-3]}')


async def main():
    async with client:
        await load_extensions()
        await client.start(TOKEN)

TOKEN = "OTk5NDQ0Mjc3MzEyNjI2ODU4.GaEnFI.UuLXTVJePra32HXGpyOcTYQdyUCo2U9nocvSr8"
asyncio.run(main())
