"""The data for the levels in the game."""

from dataclasses import dataclass
from typing import List, Tuple, Dict
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, NO_MANS_LAND_WIDTH
from entities.units import UnitType

starting_units = {
    UnitType.ARCHER: 5,
}

@dataclass
class Battle:
    id: str
    enemies: List[Tuple[UnitType, Tuple[int, int]]]
    dependencies: List[str]
    tip: List[str]

def get_battle(battle_id: str) -> Battle:
    for battle in battles:
        if battle.id == battle_id:
            return battle
    raise ValueError(f"Battle with id {battle_id} not found")

battles = [
    Battle(
        id="tutorial_1",
        enemies=[
            (UnitType.HORSEMAN, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=[
            "Left click to place/move units.",
            "Right click to return units to the barracks.",
            "",
            "Horsemen are strong against archers,",
            "but weak against groups of swordsmen.",
        ]
    ),
    Battle(
        id="tutorial_2", 
        enemies=[
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT * 1 // 8)),
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT * 7 // 8)),
        ],
        dependencies=["tutorial_1"],
        tip=[
            "Units you defeat are added to your barracks,",
            "in exchange for the units placed to defeat them.",
            "Units you don't use remain in your barracks,",
            "so the fewer you use, the more you save for later.",
            "",
            "Despite being strong in groups, swordsmen are weak individually.",
        ]
    ),
    Battle(
        id="tutorial_3",
        enemies=[
            (UnitType.FANCY_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=["tutorial_2"],
        tip=[
            "You can revisit battles you've already completed to change your solutions.",
            "This enemy is very strong against melee units, but vulnerable to archers.",
        ]
    ),
    Battle(
        id="tutorial_4",
        enemies=[
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 0 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 2 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 3 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 4 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.ARCHER, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 + BATTLEFIELD_HEIGHT // 4)),
            (UnitType.ARCHER, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 - BATTLEFIELD_HEIGHT // 4)),
        ],
        dependencies=["tutorial_3"],
        tip=[
            "In BattleSwap, you will encounter many powerful enemies",
            "who will become powerful allies after you defeat them.",
        ]
    ),
]

