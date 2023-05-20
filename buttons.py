import discord
from discord import ButtonStyle as Bstyle
from discord.ext import commands


class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    '''@discord.ui.button(label="Button", style=Bstyle.gray)
    async def gray_button(self, button: discord.ui.Button,
                          interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"This is an edited button response!")'''

    @discord.ui.button(label="Claim", custom_id="claim", style=Bstyle.green)
    async def claim_button(self, button: discord.ui.Button,
                           interaction: discord.Interaction):
        await interaction.response.send_message(content=f"changed")

    '''@discord.ui.button(label="Unclaim", custom_id="unclaim", style=Bstyle.red)
    async def unclaim_button(self, button, interaction):
        pass

    @discord.ui.button(label="Backfill", custom_id="backfill", style=Bstyle.blurple)
    async def backfill_button(self, button, interaction):
        pass

    @discord.ui.button(label="Stop", custom_id="stop", style=Bstyle.red)
    async def stop_button(self, button, interaction):
        pass'''


'''
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
                msg = await ctx.send(components=components, embed=embed)
                await btn.respond(message)
            except TimeoutError:
                await msg.delete()
'''
