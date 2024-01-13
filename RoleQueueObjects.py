import json

from discord import ui, SelectOption, Interaction
import discord

class RoleQueueSelect(ui.Select):

    def __init__(self, view_int: Interaction):
        super().__init__(
            min_values=2,
            max_values=3,
            options=[
                SelectOption(label="Tank"),
                SelectOption(label="Damage"),
                SelectOption(label="Support")
            ])
        self.view_int = view_int
        self.queues = {}

    async def callback(self, interaction: Interaction):
        with open("config.json", "r") as f:
            data = json.load(f)
            ID_TO_PLAYER = data["ID_TO_PLAYER"]
        user = interaction.user
        self.queues[ID_TO_PLAYER[str(user.id)]] = self.values
        await interaction.response.send_message(
            f"{self.values} selected for **{user.display_name}**",
            ephemeral=True,
            delete_after=3
        )
        await self.view_int.followup.send(
            content=f"Queues:\n\n{self.queues}",
            ephemeral=True
        )

