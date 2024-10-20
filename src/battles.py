"""Spawns the units for battles."""

from CONSTANTS import SCREEN_HEIGHT, SCREEN_WIDTH
from entities.units import create_swordsman, create_archer, create_mage, create_horseman, create_werebear, create_fancy_swordsman
from components.team import TeamType

battles = {}

def tutorial_1():
    # 5 archers on Team 1 vs a horsemans on Team 2
    create_archer(200, 250, TeamType.TEAM1)
    create_archer(300, 100, TeamType.TEAM1)
    create_archer(300, 150, TeamType.TEAM1)
    create_archer(300, 200, TeamType.TEAM1)
    create_archer(300, 250, TeamType.TEAM1)
    create_horseman(700, 300, TeamType.TEAM2)

battles["tutorial_1"] = tutorial_1

def tutorial_2():
    # 1 horseman on Team 1 vs 2 swordsmen (far apart) on Team 2
    create_horseman(200, 100, TeamType.TEAM1)
    create_swordsman(400, 100, TeamType.TEAM2)
    create_swordsman(400, 500, TeamType.TEAM2)

battles["tutorial_2"] = tutorial_2

def tutorial_3_failed():
    # 2 swordsman vs 1 fancy swordsman
    create_swordsman(300, 280, TeamType.TEAM1)
    create_swordsman(300, 320, TeamType.TEAM1)
    create_fancy_swordsman(500, 330, TeamType.TEAM2)

battles["tutorial_3_failed"] = tutorial_3_failed

def tutorial_1_revisited():
    # 2 swordsman (close together) vs a horsemans on Team 2
    create_swordsman(300, 280, TeamType.TEAM1)
    create_swordsman(300, 320, TeamType.TEAM1)
    create_horseman(500, 300, TeamType.TEAM2)

battles["tutorial_1_revisited"] = tutorial_1_revisited

def tutorial_3_success():
    # 4 archers vs 1 fancy swordsman
    create_archer(300, 100, TeamType.TEAM1)
    create_archer(300, 300, TeamType.TEAM1)
    create_archer(300, 500, TeamType.TEAM1)
    create_fancy_swordsman(700, 300, TeamType.TEAM2)

battles["tutorial_3_success"] = tutorial_3_success


def tutorial_finale():
    # 1 werebear vs 2 horsemen (front line) and 3 swordsman (back line)
    create_fancy_swordsman(300, 500, TeamType.TEAM1)
    create_swordsman(500, 300, TeamType.TEAM2)
    create_swordsman(550, 300, TeamType.TEAM2)
    create_swordsman(600, 300, TeamType.TEAM2)
    create_swordsman(650, 300, TeamType.TEAM2)
    create_swordsman(700, 300, TeamType.TEAM2)
    create_archer(400, 100, TeamType.TEAM2)
    create_archer(400, 500, TeamType.TEAM2)

battles["tutorial_finale"] = tutorial_finale

