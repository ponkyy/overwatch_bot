import enum
import math


class Results(enum.Enum):
    team_1 = 1
    team_2 = 2
    draw = 3
    annul = 4


class Role(enum.Enum):
    Unselected = "None"
    Tank = "Tank"
    Damage = "Damage"
    Support = "Support"


class Tier(enum.Enum):
    Bronze = "Bronze"
    Silver = "Silver"
    Gold = "Gold"
    Platinum = "Platinum"
    Diamond = "Diamond"
    Master = "Master"
    Grandmaster = "Grandmaster"
    Top_500 = "Top_500"


class Rank:
    RANK_SRS = {
        "Bronze": (0, 1499),
        "Silver": (1500, 1999),
        "Gold": (2000, 2499),
        "Platinum": (2500, 2999),
        "Diamond": (3000, 3499),
        "Master": (3500, 3999),
        "Grandmaster": (4000, 4499),
        "Top_500": (4500, 5000)
    }

    def __init__(self, name: str):
        repr = name.split()
        tier = Tier(repr[0])
        division = int(repr[1])
        self.Tier = tier
        self.Division = division

    # todo: add support for dynamic sr

    @property
    def sr(self) -> int:
        range = self.RANK_SRS[self.Tier.name]
        return math.floor(
            range[0] + (range[1] - range[0]) / 4 * (self.Division - 1))

