import discord
from discord.ext import commands, tasks
import json
from discord import ButtonStyle as BStyle
# from botbot.buttons import Buttons
from discord.ui import Button
import botbot.checks as checks
import datetime


class Overwatch(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.claims: list[str] = []
        self.backfill: list[str] = []

        '''with open('overwatch.json', 'r') as f:
            self.channels: dict[int, int] = json.load(f)'''

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def enable(self, ctx, attr=None):
        guild: str = str(ctx.guild.id)
        channel: int = ctx.channel.id

        with open('overwatch.json', 'r') as f:
            content = json.load(f)
        # not enabled in guild, or bypass enabled
        if guild not in content or attr == "-h":
            content[guild] = channel
            await ctx.send('Enabled')
        # enabled in different channel
        elif content[guild] != channel:
            await ctx.send(f'Enabled in <#{content[guild]}>')
        # already enabled in channel
        else:
            await ctx.send('Already enabled.')

        with open('overwatch.json', 'w') as f:
            json.dump(content, f, indent=4)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def disable(self, ctx):
        guild: str = str(ctx.guild.id)
        # channel: int = ctx.channel.id

        with open('overwatch.json', 'r') as f:
            content: dict[str, int] = json.load(f)

        try:
            content.pop(guild)
        except KeyError:
            await ctx.send("Already Disabled")
        else:
            with open('overwatch.json', 'w') as f:
                json.dump(content, f, indent=4)
            await ctx.send('Disabled')

    def update_embed(self, embed):
        repr_claim = "No Claims" if not self.claims \
            else '\n'.join(self.claims)
        repr_backfill = "No Backfill" if not self.backfill \
            else '\n'.join(self.backfill)

        embed.set_field_at(
            0, name="Claims",
            value=f"{repr_claim}"
        )
        embed.set_field_at(
            1, name="Backfill",
            value=f"{repr_backfill}"
        )

    @commands.command()
    #@tasks.loop(seconds=5, reconnect=True)
    async def main(self, ctx):
        Overwatch.__init__(self, self.client)
        message = 'OVERWATCH IS STARTING'
        embed = discord.Embed(
            title='Overwatch',
            description=message,
            color=0xFF5733
        )
        embed.add_field(
            name='Claims',
            value='No claims',
            inline=True
        )
        embed.add_field(
            name='Backfill',
            value='No backfill',
            inline=True
        )
        view = discord.ui.View()
        buttons = [
            (BStyle.green, "Claim", "claim"),
            (BStyle.red, "Unclaim", "unclaim"),
            (BStyle.blurple, "Backfill", "backfill"),
            (BStyle.red, "Stop", "stop"),
        ]
        items = [discord.ui.Button(style=buttons[i][0], label=buttons[i][1],
                                   custom_id=buttons[i][2]) for i in range(4)]
        for item in items:
            view.add_item(item=item)
        msg = await ctx.send(view=view, embed=embed)

        while True:
            try:
                # clicked btn
                btn = await msg.wait_for("button", self.client)
                curr_username: str = f"<@{btn.author.id}>"

                # claim
                if btn.custom_id == 'claim':

                    if curr_username in self.claims:
                        message = f"{curr_username} has already claimed."

                    elif len(self.claims) == 6:
                        await btn.respond(f"Claims are full.")

                    else:
                        if curr_username in self.backfill:
                            self.backfill.remove(curr_username)
                        self.claims.append(curr_username)

                        message = f"{curr_username} is claimed."

                # unclaim
                elif btn.custom_id == 'unclaim':

                    if curr_username in self.claims:
                        self.claims.remove(curr_username)
                        message = f"{curr_username} unclaimed."
                    elif curr_username in self.backfill:
                        self.backfill.remove(curr_username)
                        message = f"{curr_username} unclaimed."
                    else:
                        message = f"{curr_username} did not claim."

                # backfill
                elif btn.custom_id == 'backfill':

                    if curr_username in self.backfill:
                        message = f"{curr_username} is already backfilled."
                    else:
                        if curr_username in self.claims:
                            self.claims.remove(curr_username)
                        self.backfill.append(curr_username)
                        message = f"{curr_username} has backfilled."

                # stop
                elif btn.custom_id == 'stop':
                    await btn.respond("Overwatch cancelled :(")
                    await msg.delete()
                    break

                self.update_embed(embed)
                await msg.delete()
                msg = await ctx.send(view=view, embed=embed)
                await btn.respond(message)
            except TimeoutError:
                await msg.delete()

    #@checks.valid_channel()
    #@commands.has_permissions(administrator=True)
    @commands.command()
    async def start(self, ctx):
        self.main.start(ctx)

    @checks.valid_channel()
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def stop(self, ctx, attr):
        if attr == "-h":
            self.main.cancel()
        self.main.stop()


async def setup(client):
    await client.add_cog(Overwatch(client))
