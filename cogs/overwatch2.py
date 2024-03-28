import asyncio
import copy
import enum
from datetime import datetime
from itertools import combinations
import math
from multiprocessing import Pool, freeze_support
import multiprocessing
import time
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
from RoleQueueObjects import RoleQueueSelect
from new_type import *
import json
import random

class Player:
    
    def __init__(self, name: str, ranks: dict[str, str]):
        self.name = name
        self.ranks: dict[Role, Rank] = {
            Role.Tank: Rank(ranks["tank"]),
            Role.Damage: Rank(ranks["damage"]),
            Role.Support: Rank(ranks["support"])
        }
        self.queues: dict[Role, bool] = {
            Role.Tank: False,
            Role.Damage: False,
            Role.Support: False
        }
        self.role: Role = Role.Unselected

    def set_queues(self, queues: list[str]):
        for queue in queues:
            self.queues[Role(queue)] = True

    def as_role(self, role: Role):
        temp = copy.deepcopy(self)
        temp.role = role
        return temp

    def __repr__(self) -> str:
        return f"{self.name}: {self.role.name}"

class Match:

    def __init__(self, t1: list[Player], t2: list[Player]):
        self.team1 = t1
        self.team2 = t2

    def __str__(self) -> str:
        return f"{self.team1}\n{self.team2}"

    def get_avgs(self) -> dict:
        team1 = {player: player.ranks[player.role] for player in self.team1}
        team2 = {player: player.ranks[player.role] for player in self.team2}

        stats = {}
        stats['total_avg_diff'] = math.dist(
            [player.ranks[player.role].sr for player in team1],
            [player.ranks[player.role].sr for player in team2])/5

        stats['tank_diff'] = math.dist(
            [player.ranks[Role.Tank].sr for player in team1 if
             player.role == Role.Tank],
            [player.ranks[Role.Tank].sr for player in team2 if
             player.role == Role.Tank])

        stats['damage_diff'] = math.dist(
            [player.ranks[Role.Damage].sr for player in team1 if
             player.role == Role.Damage],
            [player.ranks[Role.Damage].sr for player in team2 if
             player.role == Role.Damage])/2

        stats['support_diff'] = math.dist(
            [player.ranks[Role.Support].sr for player in team1 if
             player.role == Role.Support],
            [player.ranks[Role.Support].sr for player in team2 if
             player.role == Role.Support])/2

        return stats
    def __repr__(self) -> str:
        return f"\n{[(player.name, player.role.name) for player in self.team1]} vs {[(player.name, player.role.name) for player in self.team2]}\n"

def generate_combinations(
        args: tuple[tuple[Player, Player], list[Player], list[Player]]) -> list[Match]:
    # please don't ask me to explain this I don't remember how it works
    tanks, dps_players, support_players = args
    team1_tank = tanks[0]
    team2_tank = tanks[1]
    used_players = tanks
    valid_combinations: list[Match] = []
    for team1_dps in combinations(
        [p for p in dps_players if p not in used_players], 2):
        used_players = tanks + tuple(team1_dps)
        for team2_dps in combinations(
            [p for p in dps_players if p not in used_players], 2):
            used_players = tanks + tuple(team1_dps) + tuple(team2_dps)
            for team1_support in combinations([p for p in support_players if p not in used_players], 2):
                for team2_support in combinations([p for p in support_players if p not in used_players + tuple(team1_support)], 2):
                    team1 = [team1_tank.as_role(Role.Tank)] + [
                    p.as_role(Role.Damage) for p in team1_dps] + [
                    p.as_role(Role.Support) for p in team1_support]
                    team2 = [team2_tank.as_role(Role.Tank)] + [
                    p.as_role(Role.Damage) for p in team2_dps] + [
                    p.as_role(Role.Support) for p in team2_support]
                    valid_combinations.append(Match(team1, team2))
    return valid_combinations


def generate_team_combos(players: list[Player]):
    valid_combinations: list[Match] = []

    # Separate players into role-specific lists
    tank_players = [player for player in players if player.queues[Role.Tank]]
    dps_players = [player for player in players if player.queues[Role.Damage]]
    support_players = [player for player in players if player.queues[Role.Support]]
    tank_combinations = [t for t in combinations(tank_players, 2)]
    random.shuffle(tank_combinations)
    # Generate combinations with role constraints
    args_list = [[tanks, support_players, dps_players] for tanks in tank_combinations]
    start = time.time()

    # Create a multiprocessing pool
    with multiprocessing.Pool() as pool:
        results = pool.imap_unordered(generate_combinations, args_list)
        for result in results:
            valid_combinations.extend(result)

    print(f"Generation took {(time.time() - start)}s")

    return valid_combinations


with open("config.json", "r") as f:
    data = json.load(f)
    RANKS = data["RANKS"]
    URL = data["URL"]

with open("players.json", "r") as f:
    PLAYER_DATA: dict[str, dict[str, str]] = json.load(f)
    Players = [Player(name, data) for name, data in PLAYER_DATA.items()]

PlayerChoices = enum.Enum("PlayerChoices", list(PLAYER_DATA.keys()))


class Overwatch(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.active = False
        self.queues = {}
        self.role_emojis = {
            Tier.Bronze: "<:Bronze:1109603963424215060>",
            Tier.Silver: "<:Silver:1109603962128171128>",
            Tier.Gold: "<:Gold:1109603960333013083>",
            Tier.Platinum: "<:Platinum:1109603959137644695>",
            Tier.Diamond: "<:Diamond:1109604516757770281>",
            Tier.Master: "<:Master:1109603953886380174>",
            Tier.Grandmaster: "<:Grandmaster:1109604769963716688>",
            Tier.Top_500: "<:Top500:1109604938297905293>",
        }
        self.players: list[Player] = []

    def _get_emoji(self, player : Player, role:Role) -> str:
        return self.role_emojis[player.ranks[role].Tier]

    async def role_queue(self, interaction: discord.Interaction,
                         timeout: int) -> dict[str, list[Role]]:
        view = discord.ui.View()
        select = RoleQueueSelect(interaction)
        view.add_item(select)
        await interaction.response.send_message("Choose role queues", view=view)
        i = timeout
        msg = await interaction.followup.send(content=".")
        while i >= 0:
            await interaction.followup.edit_message(
                msg.id, content=f"**({i} seconds remaining)**")
            await asyncio.sleep(1)
            i -= 1
        interaction.is_expired()
        await asyncio.sleep(2)
        await interaction.followup.delete_message(msg.id)
        await interaction.delete_original_response()
        return select.queues

    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.command(
        name="overwatch5v5",
        description="Creates a 5v5 matchup for Overwatch"
    )
    @app_commands.describe(timeout="Time to select role")
    async def overwatch(self, interaction: discord.Interaction,
                        timeout: app_commands.Range[int, 5, 120] = 15) -> None:

        if self.active:
            await interaction.response.send_message(
                "A game is currently active. This command has no effect",
                ephemeral=True
            )
            return

        p = list(PLAYER_DATA.keys())

        queues = await self.role_queue(interaction, timeout)
        if len(queues) < 10:
            await interaction.followup.send(
                f"Not enough players queued: **{len(queues)} queued**")
            return

        self.players = [player for player in Players if
                        player.name in queues.keys()]
        for player in self.players:
            player.set_queues(queues[player.name])
        possible_matches = generate_team_combos(self.players)

        good_matches: list[Match] = []
        while len(possible_matches) > 0:
            current_match = possible_matches.pop()
            _stats = current_match.get_avgs()
            if _stats['total_avg_diff'] < 280 and _stats['tank_diff'] < 280 and \
                    _stats['damage_diff'] < 500 and _stats['support_diff'] < 500:
                good_matches.append(current_match)

        chosen_match = random.choice(good_matches)
        stats = chosen_match.get_avgs()
        team_1 = "\n\t\t".join([
            f"__{player.name}__: {player.role} {self._get_emoji(player, player.role)}"
            for player in chosen_match.team1])
        team_2 = "\n\t\t".join([
            f"__{player.name}__: {player.role} {self._get_emoji(player, player.role)}"
            for player in chosen_match.team2])

        msg = f"**__Match Average__: N/A**\n\n" \
              f"**Team 1:**\n\t\t{team_1}\n" \
              f"**Team 2:**\n\t\t{team_2}\n\n" \
              f"Tank difference: {stats['tank_diff']}\n" \
              f"Damage difference: {stats['damage_diff']}\n" \
              f"Support difference: {stats['support_diff']}\n" \
              f"**__Total team difference__**: {stats['total_avg_diff']:.3f}\n"

        await interaction.followup.send(msg)
        self.active = True

    @app_commands.command(
        name="show_ranks",
        description="Shows ranks of all players"
    )
    async def show_ranks(self, interaction: discord.Interaction):
        with open("players.json", "r") as f:
            self.players = json.load(f)
        data = []
        for player in Players:
            e1 = self._get_emoji(player, Role.Tank)
            e2 = self._get_emoji(player,Role.Damage)
            e3 = self._get_emoji(player, Role.Support)
            data.append(f"**{player}**\n\tT - {e1} D - {e2} S - {e3}")
        data = "\n".join(data)
        await interaction.response.send_message(data, ephemeral=True)

    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.command(name="role_queue_test", description="Set role queues")
    async def role_queue_test(self, interaction: discord.Interaction):
        await self.role_queue(interaction, 5)

    @app_commands.command(
        name="matchups_link",
        description="Presents button with link to matchups page")
    async def get_matchups_link(self, interaction: discord.Interaction):

        button = discord.ui.Button(
            label="To Matchups",
            style=discord.ButtonStyle.url,
            url=URL)
        view = discord.ui.View(timeout=10)
        view.add_item(button)
        await interaction.response.send_message(
            "Click button to visit the matchups page",
            view=view,
            delete_after=10
        )

    @app_commands.command(
        name="end_game",
        description="Ends an active 5v5 matchup"
    )
    @app_commands.describe(result="Result of the match")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def end_game(self, interaction: discord.Interaction,
                       result: Results,
                       capture_1: Optional[int] = None,
                       capture_2: Optional[int] = None,
                       distance_1: Optional[int] = None,
                       distance_2: Optional[int] = None
                       ):
        if not self.active:
            await interaction.response.send_message(
                "There is no active game. This command has no effect",
                ephemeral=True
            )
            return
        if result == Results.annul:
            await interaction.response.send_message("Match annulled!",
                                                    ephemeral=True)
            self.active = False
            return
        elif result == Results.team_1:
            winner = "Team 1 has won the match!"
        elif result == Results.team_2:
            winner = "Team 2 has won the match!"
        else:
            winner = "The match has resulted in a draw!"

        with open("match_information.json", "r") as f:
            data = json.load(f)["MATCH_HISTORY"]
            matches = data["MATCHES"]
            total = data["TOTAL"] + 1

        now = datetime.now()

        curr_match = {
            "id": total,
            "date": now.strftime("%d-%m-%Y %H:%M:%S"),
            "team_1": "team_1",
            "team_2": "team_2",
            "result": result.name,
        }
        matches.append(curr_match)
        with open("match_information.json", "w") as f:

            data["MATCHES"] = matches
            data["TOTAL"] = total
            json.dump(data, f, indent=4)

        await interaction.response.send_message(f"{winner}\n{curr_match}")
        self.active = False

    @app_commands.command(name="set_user_to_player",
                          description="Associates a user to an Overwatch username")
    @app_commands.describe(user="User", player="Player")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def set_user_to_player(self, interaction: discord.Interaction,
                                 user: discord.Member, player: PlayerChoices):

        with open("config.json", "r") as f:
            data = json.load(f)
            id_to_player = data["ID_TO_PLAYER"]
        id = str(user.id)
        if id not in id_to_player:
            id_to_player[id] = player.name
            with open("config.json", "w") as f:
                json.dump(data, f, indent=4)
            await interaction.response.send_message(
                f"**{user.display_name}** successfully set to **{player.name}**",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                f"**{user.display_name}** already set to **{id_to_player[id]}**",
                ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Overwatch(client))