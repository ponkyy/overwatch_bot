import asyncio
import enum
import json
import random
from datetime import datetime
from itertools import combinations
from typing import Optional
from multiprocessing import Pool
import discord
from discord import app_commands
from discord.ext import commands
import time

from RoleQueueObjects import RoleQueueSelect

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


class Bool(enum.Enum):
    false = 0
    true = 1


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

    def as_role(self, role: str):
        temp = Player(self.name, self.queues)
        temp.role = role
        return temp

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

def generate_combinations(args):
    tanks, dps_players, support_players = args
    team1_tank = tanks[0]
    team2_tank = tanks[1]
    used_players = tanks
    valid_combinations = []
    for team1_dps in combinations([p for p in dps_players if p not in used_players], 2):
        used_players = tanks + team1_dps
        for team2_dps in combinations([p for p in dps_players if p not in used_players], 2):
            used_players = tanks + team1_dps + team2_dps
            for team1_support in combinations([p for p in support_players if p not in used_players], 2):
                used_players = tanks + team1_dps + team2_dps + team1_support
                team2_support = [p for p in support_players if p not in used_players]
                team1 = [team1_tank.as_role("tank")] + [p.as_role("dps") for p in team1_dps] + [
                    p.as_role("support") for p in team1_support]
                team2 = [team2_tank.as_role("tank")] + [p.as_role("dps") for p in team2_dps] + [
                    p.as_role("support") for p in team2_support]
                valid_combinations.append((team1, team2))
    return valid_combinations
def generate_team_combos(players: list[Player]):
    valid_combinations = []

    # Separate players into role-specific lists
    tank_players = [player for player in players if player.queues[0]]
    dps_players = [player for player in players if player.queues[1]]
    support_players = [player for player in players if player.queues[2]]

    # Generate combinations with role constraints
    args_list = [[tanks, support_players, dps_players] for tanks in combinations(tank_players, 2)]
    start = time.time()
    with Pool(12) as p:
        results = p.map(generate_combinations, args_list)
        p.close()
        p.join()
        for result in results:
            valid_combinations.extend(result)
    print(time.time() - start)

    return valid_combinations


class Match:

    def __init__(self, players: list[Player]):
        self.players = players
        self.team_1: list[Player] = []
        self.team_2: list[Player] = []
        self.roles: dict[str, list[Player]] = {
            "Tank": [],
            "Damage": [],
            "Support": []
        }
        #self.make_teams()

    def make_teams(self) -> int:

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
                return 1  # teams made improperly

            self.roles[player.role].append(player)
            weights[list(self.roles.keys()).index(player.role)] -= 1

        self.team_1.extend(self.roles["Tank"][:1])
        self.team_1.extend(self.roles["Damage"][:2])
        self.team_1.extend(self.roles["Support"][:2])
        self.team_2.extend(self.roles["Tank"][1:])
        self.team_2.extend(self.roles["Damage"][2:])
        self.team_2.extend(self.roles["Support"][2:])
        return 0

    def __str__(self) -> str:
        return f"{self.team_1}\n{self.team_2}"


class Comp:

    def __init__(self, comp: list, players: dict):
        self.t1 = comp[:5]
        self.t2 = comp[5:10]
        self._get_avgs(players)

    def _get_avgs(self, players):
        self.stats = {}

        self.team_avg_1 = sum([
            int(RANKS[players[self.t1[0]]["tank"]]) * 1.1,
            int(RANKS[players[self.t1[1]]["damage"]]),
            int(RANKS[players[self.t1[2]]["damage"]]),
            int(RANKS[players[self.t1[3]]["support"]]),
            int(RANKS[players[self.t1[4]]["support"]])
        ]) / 5

        self.team_avg_2 = sum([
            int(RANKS[players[self.t2[0]]["tank"]]) * 1.1,
            int(RANKS[players[self.t2[1]]["damage"]]),
            int(RANKS[players[self.t2[2]]["damage"]]),
            int(RANKS[players[self.t2[3]]["support"]]),
            int(RANKS[players[self.t2[4]]["support"]])
        ]) / 5

        self.stats['total_avg_diff'] = abs(self.team_avg_1 - self.team_avg_2)

        self.stats['tank_diff'] = abs(int(RANKS[players[self.t1[0]]["tank"]]) -
                                      int(RANKS[players[self.t2[0]]["tank"]]))

        self.stats['damage_diff'] = abs(
            (int(RANKS[players[self.t1[1]]["damage"]]) +
             int(RANKS[players[self.t1[2]]["damage"]])) / 2 -
            (int(RANKS[players[self.t2[1]]["damage"]]) +
             int(RANKS[players[self.t2[2]]["damage"]])) / 2)

        self.stats['support_diff'] = abs(
            (int(RANKS[players[self.t1[3]]["support"]]) +
             int(RANKS[players[self.t1[4]]["support"]])) / 2
            - (int(RANKS[players[self.t2[3]]["support"]]) +
               int(RANKS[players[self.t2[4]]["support"]])) / 2)

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
        }
        self.players = PLAYERS

    def _get_emoji(self, name, role) -> str:
        return self.role_emojis[self.players[name][role.lower()][:-2]]

    async def role_queue(self, interaction: discord.Interaction, timeout: int):
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
    @app_commands.describe(timeout="Time to select role", flex="For testing") # to become for flexing
    async def overwatch(self, interaction: discord.Interaction,
                        timeout: app_commands.Range[int, 5, 120] = 15,
                        flex: Bool = Bool.false) -> None:

        if self.active:
            await interaction.response.send_message(
                "A game is currently active. This command has no effect",
                ephemeral=True
            )
            return

        p = list(PLAYERS.keys())
        if flex == Bool.true: # for testing cuz i dont wanna make proper test :D
            await interaction.response.defer()
            queues: dict[str, list[str]] = {player: ['Damage', 'Support'] for player in p}
            queues["ponky"] = ['Tank', 'Damage', 'Support']
            queues["trk20"] = ['Tank', 'Damage', 'Support']
        else:
            queues = await self.role_queue(interaction, timeout)

        if len(queues) < 10:
            await interaction.followup.send(f"Not enough players queued: **{len(queues)} queued**")
            return

        bad_teams = 0
        while bad_teams != 1000:
            random.shuffle(p)
            players = [Player(player, queues[player]) for player in p[:10]]
            match = Match(players)
            if match.make_teams() == 1:  # teams were not made well
                bad_teams += 1
                continue
            # await interaction.response.send_message(str(match))

            # Turn the match to being readable by Comp

            match_comp = match.team_1 + match.team_2
            match_comp = [repr(x) for x in match_comp]
            curr = Comp(match_comp, self.players)
            if curr.stats['total_avg_diff'] < 0.5 and curr.stats[
                'tank_diff'] <= 5 and \
                    curr.stats['damage_diff'] <= 5 and curr.stats[
                'support_diff'] <= 5:
                break
            #bad_teams += 1  #  likely required in timeout cases
            #  i should really make this not rely so heavily on randomness
        else:  # did not break and thus bad_teams reached limit
            await interaction.followup.send("Unable to form teams. Try again")
            return

        roles = ["Tank", "Damage", "Damage", "Support", "Support"]
        team_1, team_2 = [], []

        for i in range(5):
            r = roles[i]
            c1 = curr.t1[i]
            c2 = curr.t2[i]
            e1 = self._get_emoji(c1, r)
            e2 = self._get_emoji(c2, r)
            team_1.append(f"__{c1}__: {r} {e1}")
            team_2.append(f"__{c2}__: {r} {e2}")

        team_1 = "\n\t\t".join(team_1)
        team_2 = "\n\t\t".join(team_2)

        msg = f"**__Match Average__: N/A**\n\n" \
              f"**Team 1:**\n\t\t{team_1}\n" \
              f"**Team 2:**\n\t\t{team_2}\n\n" \
              f"Tank difference: {curr.stats['tank_diff']}\n" \
              f"Damage difference: {curr.stats['damage_diff']}\n" \
              f"Support difference: {curr.stats['support_diff']}\n" \
              f"**__Total team difference__**: {curr.stats['total_avg_diff']:.3f}\n" \
              f"{bad_teams=}"


        await interaction.followup.send(msg)
        self.active = True

    @app_commands.command(
        name="show_ranks",
        description="Shows ranks of all players"
    )
    async def show_ranks(self, interaction: discord.Interaction):

        data = []
        for player in self.players:
            e1 = self._get_emoji(player, "tank")
            e2 = self._get_emoji(player, "damage")
            e3 = self._get_emoji(player, "support")
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
    @app_commands.describe(user="User")
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
