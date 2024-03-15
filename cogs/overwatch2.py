import asyncio
import enum
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
from RoleQueueObjects import RoleQueueSelect, StartButton
import json
import random

with open("config.json", "r") as f:
    data = json.load(f)
    RANKS = data["RANKS"]
    URL = data["URL"]

with open("players.json", "r") as f:
    PLAYERS: dict[str, dict[str, str]] = json.load(f)


class Results(enum.Enum):
    team_1 = 1
    team_2 = 2
    draw = 3
    annul = 4


PlayerChoices = enum.Enum("PlayerChoices", list(PLAYERS.keys()))


class Player:

    def __init__(self, name: str, queues: list[str]):
        self.name = name
        self.queues = [True, True, True]
        if len(queues) != 3:
            if "Tank" not in queues:
                self.queues[0] = False
            elif "Damage" not in queues:
                self.queues[1] = False
            elif "Support" not in queues:
                self.queues[2] = False
        self.role: Optional[str] = None

    def __repr__(self) -> str:
        return self.name

    def adjust(self, weights: list[int]):
        curr = []
        for i in range(3):
            if self.queues[i]:
                curr.append(weights[i])
            else:
                curr.append(0)
        return curr


class Match:

    def __init__(self, players: list[Player]):
        self.players = players
        self.t1: list[Player] = []
        self.t2: list[Player] = []
        self.roles: dict[str, list[Player]] = {
            "Tank": [],
            "Damage": [],
            "Support": []
        }

    def make_teams(self) -> bool:

        weights = [2, 4, 4]
        for player in self.players:
            if weights == [0, 0, 0]:  # no more general slots available
                break  # teams made properly
            curr_weights = player.adjust(weights)
            '''if curr_weights == [0, 0, 0]:  # no more valid queue slots available
                pass'''
            try:
                player.role = random.choices(["Tank", "Damage", "Support"],
                                             weights=curr_weights, k=1)[0]
            except ValueError:
                return True  # teams made improperly

            self.roles[player.role].append(player)
            weights[list(self.roles.keys()).index(player.role)] -= 1

        self.t1.extend(self.roles["Tank"][:1])
        self.t1.extend(self.roles["Damage"][:2])
        self.t1.extend(self.roles["Support"][:2])
        self.t2.extend(self.roles["Tank"][1:])
        self.t2.extend(self.roles["Damage"][2:])
        self.t2.extend(self.roles["Support"][2:])
        return False

    def __str__(self) -> str:
        return f"{self.t1}\n{self.t2}"

    def _get_rank(self, t, i, role):
        return int(RANKS[PLAYERS[t[i].name][role]])

    def get_avgs(self) -> dict:

        tank1 = self._get_rank(self.t1, 0, "tank")
        tank2 = self._get_rank(self.t2, 0, "tank")
        dam1 = self._get_rank(self.t1, 1, "damage")
        dam2 = self._get_rank(self.t1, 2, "damage")
        dam3 = self._get_rank(self.t2, 1, "damage")
        dam4 = self._get_rank(self.t2, 2, "damage")
        sup1 = self._get_rank(self.t1, 3, "support")
        sup2 = self._get_rank(self.t1, 4, "support")
        sup3 = self._get_rank(self.t2, 3, "support")
        sup4 = self._get_rank(self.t2, 4, "support")

        stats = {}
        team_avg_1 = sum([tank1, dam1, dam2, sup1, sup2]) / 5

        team_avg_2 = sum([tank2, dam3, dam4, sup3, sup4]) / 5

        stats['total_avg_diff'] = abs(team_avg_1 - team_avg_2)

        stats['tank_diff'] = abs(tank1 - tank2)

        stats['damage_diff'] = abs(dam1 + dam2 - dam3 - dam4) / 2

        stats['support_diff'] = abs(sup1 + sup2 - sup3 - sup4) / 2

        return stats
        # self.avg = list(ranks.keys())[
        # list(ranks.values()).index(str(round(self.avg_1)))]


class Overwatch(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.active = False
        self.queues = {}
        self.role_emojis = {
            "Bronze": "<:Bronze:1109603963424215060>",
            "Silver": "<:Silver:1109603962128171128>",
            "Gold": "<:Gold:1109603960333013083>",
            "Platinum": "<:Platinum:1109603959137644695>",
            "Diamond": "<:Diamond:1109604516757770281>",
            "Master": "<:Master:1109603953886380174>",
            "Grandmaster": "<:Grandmaster:1109604769963716688>",
            "Top 500": "<:Top500:1109604938297905293>",
            "NO RANK SKILL ISSUE": "NO RANK SKILL ISSUE"
        }
        self.players = PLAYERS

    def _get_rank(self, name, role) -> str:
        rank = self.players[name][role.lower()]
        return f"{self.role_emojis[rank[:-2]]} **{rank[-1]}**"

    async def role_queue(self, interaction: discord.Interaction):
        view = discord.ui.View()
        select = RoleQueueSelect(interaction)
        view.add_item(select)
        await interaction.response.send_message(select.queue_msg, view=view)
        i = 40
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
    #@app_commands.describe(timeout="Time to select role")
    async def overwatch(self, interaction: discord.Interaction) -> None:



        if self.active:
            await interaction.response.send_message(
                "A game is currently active. This command has no effect",
                ephemeral=True
            )
            return

        p = list(PLAYERS.keys())

        queues = await self.role_queue(interaction)
        if len(queues) < 10:
            await interaction.followup.send(
                f"Not enough players queued: **{len(queues)} queued**")
            return

        p = list(queues.keys())

        bad_teams = 0
        while bad_teams != 1000:
            random.shuffle(p)
            players = [Player(player, queues[player]) for player in p]
            match = Match(players)
            if match.make_teams():  # teams were not made well
                bad_teams += 1
                continue
            # await interaction.response.send_message(str(match))

            # Turn the match to being readable by Comp

            '''match_comp = match.team_1 + match.team_2
            match_comp = [repr(x) for x in match_comp]'''
            try:
                stats = match.get_avgs()
            except KeyError as e:
                print(self.players)
                print(e)
                return
            if stats['total_avg_diff'] < 0.5 and stats[
                'tank_diff'] <= 3 and \
                    stats['damage_diff'] <= 3 and stats[
                'support_diff'] <= 3:
                break
            # bad_teams += 1  #  likely required in timeout cases
            #  i should really make this not rely so heavily on randomness
        else:  # did not break and thus bad_teams reached limit
            await interaction.followup.send("Unable to form teams. Try again")
            return

        roles = ["Tank", "Damage", "Damage", "Support", "Support"]
        team_1, team_2 = [], []

        for i in range(5):
            r = roles[i]
            c1 = match.t1[i].name
            c2 = match.t2[i].name
            e1 = self._get_rank(c1, r)
            e2 = self._get_rank(c2, r)
            team_1.append(f"__{c1}__: {r} {e1}")
            team_2.append(f"__{c2}__: {r} {e2}")

        team_1 = "\n\t\t".join(team_1)
        team_2 = "\n\t\t".join(team_2)

        msg = f"**__Match Average__: N/A**\n\n" \
              f"**Team 1:**\n\t\t{team_1}\n" \
              f"**Team 2:**\n\t\t{team_2}\n\n" \
              f"Tank difference: {stats['tank_diff']}\n" \
              f"Damage difference: {stats['damage_diff']}\n" \
              f"Support difference: {stats['support_diff']}\n" \
              f"**__Total team difference__**: {stats['total_avg_diff']:.3f}\n" \
              f"{bad_teams=}"

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
        for player in self.players:
            e1 = self._get_rank(player, "tank")
            e2 = self._get_rank(player, "damage")
            e3 = self._get_rank(player, "support")
            data.append(f"**{player}**\n\tT - {e1}  D - {e2}  S - {e3}")
        #data.sort(key=lambda x: sum())
        data = "\n".join(data)
        await interaction.response.send_message(data)

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


'''import json
import os
import new
import random

clear = lambda: os.system('clear')


def display_teams(team_1, team_2):
    print("Team 1: ")
    for role in team_1:
        print(f"\t{role}: {team_1[role]}")
    print("\n\nTeam 2: ")
    for role in team_2:
        print(f"\t{role}: {team_2[role]}")


def make_game(rank_nums):
    with open("players.json", 'r') as f:
        players = json.load(f)

    comps = new.alg(players)
    s = random.sample(comps, k=10)
    for i in range(10):
        curr = s[i]
        print(
            f"Team 1: {curr.t1} ({curr.avg_1})\nTeam 2: {curr.t2} ({curr.avg_2})\n")


def add_player(name, tank, damage, support):
    with open("players.json", 'r') as f:
        players = json.load(f)
    if name not in players:
        players[name] = {
            "tank": tank,
            "damage": damage,
            "support": support,
        }
        with open("players.json", 'w') as f:
            json.dump(players, f, indent=4)


def update_player(name, tank, damage, support):
    with open("players.json", 'r') as f:
        players = json.load(f)
    if name in players:
        d = players[name]
        if tank:
            d["tank"] = tank
        if damage:
            d["damage"] = damage
        if support:
            d["support"] = support
        with open("players.json", 'w') as f:
            json.dump(players, f, indent=4)


def display(players):
    for name in players:
        d = players[name]
        tank = d["tank"]
        damage = d["damage"]
        support = d["support"]
        print(f"{name}:\n\tTank: {tank}\n\tDamage: {damage}\n\tSupport: {support}")'''

'''def main():

    with open("ranks.json", 'r') as f:
        rank_nums = json.load(f)

    while True:
        print("Welcome to the Cadoocraft OW2 5v5 matchmaker!\n")
        option = input(
            "1. Make game\n2. Display players\n3. Add player\n4. Update player\n\n Press any other button to quit: "
        )
        clear()
        if option == "1":
            make_game(rank_nums)
            input("Done")
            clear()
        elif option == "2":
            with open("players.json") as f:
                players = json.load(f)
            display(players)
            input("\n\nPress enter to close ")
            clear()
        elif option == "3":
            name = input("Enter name: ")
            tank = input("\nEnter tank rank: ")
            damage = input("\nEnter damage rank: ")
            support = input("\nEnter support rank: ")

            if tank not in rank_nums:
                tank = None
            if damage not in rank_nums:
                damage = None
            if support not in rank_nums:
                support = None

            add_player(name, tank, damage, support)
            clear()
        elif option == "4":
            name = input("Enter name: ")
            tank = input("\nEnter tank rank: ")
            damage = input("\nEnter damage rank: ")
            support = input("\nEnter support rank: ")

            if tank not in rank_nums:
                tank = None
            if damage not in rank_nums:
                damage = None
            if support not in rank_nums:
                support = None
            update_player(name, tank, damage, support)
            clear()
        else:
            break


if __name__ == "__main__":
    main()
'''
