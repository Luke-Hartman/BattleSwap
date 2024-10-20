"""Spawns the units for battles."""

from CONSTANTS import SCREEN_HEIGHT, SCREEN_WIDTH
from entities.units import create_swordsman, create_archer, create_mage, create_horseman, create_werebear, create_fancy_swordsman
from components.team import TeamType
from components.unit_state import UnitState, State

battles = {}

def tutorial_1():
    # 5 archers on Team 1 vs a horsemans on Team 2
    create_archer(200, 250, TeamType.TEAM1),
    create_archer(300, 100, TeamType.TEAM1),
    create_archer(300, 150, TeamType.TEAM1),
    create_archer(300, 200, TeamType.TEAM1),
    create_archer(300, 250, TeamType.TEAM1),
    create_horseman(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2, TeamType.TEAM2)

battles["tutorial_1"] = tutorial_1

def tutorial_1_revisited():
    # 2 swordsman (close together) vs a horsemans on Team 2
    ...

battles["tutorial_1_revisited"] = tutorial_1_revisited

def tutorial_2():
    # 1 horseman on Team 1 vs 2 swordsmen (far apart) on Team 2
    ...

battles["tutorial_2"] = tutorial_2

def tutorial_3_failed():
    # 2 swordsman vs werebear
    ...

battles["tutorial_3_failed"] = tutorial_3_failed

def tutorial_3_success():
    # 4 archers vs 1 werebear
    ...

battles["tutorial_3_success"] = tutorial_3_success

def tutorial_3_alt_failed():
    # 2 swordsman vs 1 fancy swordsman
    ...

battles["tutorial_3_alt_failed"] = tutorial_3_alt_failed

def tutorial_3_alt_success():
    # 4 archers vs 1 fancy swordsman
    ...

battles["tutorial_3_alt_success"] = tutorial_3_alt_success
