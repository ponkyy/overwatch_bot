
class Match:

    def __init__(self):
        self.team_1: list[Player] = []
        self.team_2: list[Player] = []


class Player:

    def __init__(self, name: str, queues: list[str]):
        self.name = name
        self.queues = queues
