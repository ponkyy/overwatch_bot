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
        self.queues = {}

        with open("config.json", "r") as f:
            data = json.load(f)
            self.ID_TO_PLAYER = data["ID_TO_PLAYER"]

        self.queue_msg = self._make_queue_str()
        self.view_int = view_int


    def _make_queue_str(self):

        str_builder = []

        role_to_emoji = {
            'Tank' : ':regional_indicator_t:',
            'Damage' : ':regional_indicator_d:',
            'Support' : ':regional_indicator_s:',
        }

        for _id in self.ID_TO_PLAYER:
            player = self.ID_TO_PLAYER[_id]
            roles_chosen = self.queues.get(player)
            if roles_chosen:
                roles = "".join([role_to_emoji[role] for role in roles_chosen])
                emojis = f"{roles}✅"
            else:
                emojis = '❌'
            str_builder.append(f"{player}: {emojis}")

        return "\n".join(str_builder)

    async def callback(self, interaction: Interaction):

        user = interaction.user
        self.queues[self.ID_TO_PLAYER[str(user.id)]] = self.values
        await interaction.response.send_message(
            f"{self.values} selected for **{user.display_name}**",
            ephemeral=True, delete_after=3
        )
        await self.view_int.edit_original_response(
            content=f"Queues:\n\n{self._make_queue_str()}"
        )

