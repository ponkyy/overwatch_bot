import discord
import json
import random
from discord.ext import commands


class Comp:

    t1: list
    t2: list
    avg_1: float
    avg_2: float

    def __init__(self, comp: list, players: dict):
        self.t1 = comp[:5]
        self.t2 = comp[5:]
        self._get_avgs(players)

    def _get_avgs(self, players):
        with open("ranks.json", "r") as f:
            ranks = json.load(f)

        self.avg_1 = sum([
            int(ranks[players[self.t1[0]]["tank"]]),
            int(ranks[players[self.t1[1]]["damage"]]),
            int(ranks[players[self.t1[2]]["damage"]]),
            int(ranks[players[self.t1[3]]["support"]]),
            int(ranks[players[self.t1[4]]["support"]])
        ]) / 5
        self.avg_2 = sum([
            int(ranks[players[self.t2[0]]["tank"]]),
            int(ranks[players[self.t2[1]]["damage"]]),
            int(ranks[players[self.t2[2]]["damage"]]),
            int(ranks[players[self.t2[3]]["support"]]),
            int(ranks[players[self.t2[4]]["support"]])
        ]) / 5
        self.avg = list(ranks.keys())[list(ranks.values()).index(2)]


def alg(players):
    p = list(players.keys())
    while True:
        random.shuffle(p)
        curr = Comp(p, players)
        if curr.avg_1 == curr.avg_2:
            break

    roles = ["Tank", "Damage", "Damage", "Support", "Support"]
    team_1 = "\n\t\t".join([f"*{roles[i]}*: {curr.t1[i]}" for i in range(5)])
    team_2 = "\n\t\t".join([f"*{roles[i]}*: {curr.t2[i]}" for i in range(5)])
    #msg = f"**Team 1: \t({curr.avg_1} avg)**\n\t\t{team_1} \n**Team 2: \t({curr.avg_2} avg)**\n\t\t{team_2}\n"
    msg = f"**__Match Average__: {curr.avg}**\n\n**Team 1:**\n\t\t{team_1} \n**Team 2:**\n\t\t{team_2}\n"
    #print(msg)
    return msg


class Overwatch2(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open("players.json", 'r') as f:
            self.players = json.load(f)
        '''with open("ranks.json", 'r') as f:
            self.ranks = json.load(f)'''

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def overwatch(self, ctx):
        msg = alg(self.players)
        await ctx.send(msg)


async def setup(client):
    await client.add_cog(Overwatch2(client))



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
