import json

from discord import ui, SelectOption, Interaction
import discord

from cogs.overwatch2 import Role

with open("config.json", "r") as f:
    data = json.load(f)
    ID_TO_PLAYER = data["ID_TO_PLAYER"]


class RoleQueueSelect(ui.Select):

    def __init__(self, view_int: Interaction):
        super().__init__(
            min_values=2,
            max_values=3,
            options=[
                SelectOption(label="Tank",value=Role.Tank),
                SelectOption(label="Damage",value=Role.Damage),
                SelectOption(label="Support",value=Role.Support)
            ])
        self.view_int = view_int
        self.queues : dict[str, list[Role]] = {}

    async def callback(self, interaction: Interaction):
        user = interaction.user
        self.queues[ID_TO_PLAYER[str(user.id)]] = [Role(queue) for queue in self.values]
        await interaction.response.send_message(
            f"{self.values} selected for **{user.display_name}**",
            ephemeral=True,
            delete_after=3
        )
        await self.view_int.followup.send(
            content=f"Queues:\n\n{self.queues}",
            ephemeral=True
        )

