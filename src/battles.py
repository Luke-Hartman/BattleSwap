"""The data for the levels in the game."""

from dataclasses import dataclass
from typing import List, Tuple, Dict
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, NO_MANS_LAND_WIDTH
from entities.units import UnitType

starting_units = {
    UnitType.CORE_ARCHER: 10,
    UnitType.CORE_DUELIST: 10,
    UnitType.CORE_MAGE: 10,
    UnitType.CORE_HORSEMAN: 10,
    UnitType.CORE_SWORDSMAN: 10,
    UnitType.CRUSADER_BLACK_KNIGHT: 10,
    UnitType.CRUSADER_CLERIC: 10,
    UnitType.CRUSADER_COMMANDER: 10,
    UnitType.CRUSADER_DEFENDER: 10,
    UnitType.CRUSADER_GOLD_KNIGHT: 10,
    UnitType.CRUSADER_LONGBOWMAN: 10,
    UnitType.CRUSADER_PALADIN: 10,
    UnitType.CRUSADER_PIKEMAN: 10,
    UnitType.WEREBEAR: 10,
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
            (UnitType.CORE_HORSEMAN, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=["TODO REMOVE ME"],
        tip=[
            "Left click to place/move units.",
            "Right click to return units to the barracks.",
            "",
            "Horsemen are strong against archers, but weak against groups of swordsmen.",
        ]
    ),
    Battle(
        id="tutorial_2", 
        enemies=[
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT * 1 // 8)),
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT * 7 // 8)),
        ],
        dependencies=["tutorial_1"],
        tip=[
            "Units you defeat are added to your barracks, in exchange for the units placed to defeat them.",
            "Units you don't use remain in your barracks, so the fewer you use, the more you save for later.",
            "",
            "Despite being strong in groups, swordsmen are weak individually.",
        ]
    ),
    Battle(
        id="tutorial_3",
        enemies=[
            (UnitType.CORE_DUELIST, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
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
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 0 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 2 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 3 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 4 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CORE_ARCHER, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 + BATTLEFIELD_HEIGHT // 4)),
            (UnitType.CORE_ARCHER, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 - BATTLEFIELD_HEIGHT // 4)),
        ],
        dependencies=["tutorial_3"],
        tip=[
            "In BattleSwap, you will encounter many powerful enemies",
            "who will become powerful allies after you defeat them.",
        ]
    ),
    Battle(
        id="core_archer",
        enemies=[
            (UnitType.CORE_ARCHER, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="core_duelist",
        enemies=[
            (UnitType.CORE_DUELIST, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="core_mage",
        enemies=[
            (UnitType.CORE_MAGE, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="core_horseman",
        enemies=[
            (UnitType.CORE_HORSEMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="core_swordman",
        enemies=[
            (UnitType.CORE_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),  
    Battle(
        id="crusader_black_knight",
        enemies=[
            (UnitType.CRUSADER_BLACK_KNIGHT, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="crusader_gold_knight",
        enemies=[
            (UnitType.CRUSADER_GOLD_KNIGHT, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="crusader_longbowman",
        enemies=[
            (UnitType.CRUSADER_LONGBOWMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="crusader_paladin",
        enemies=[
            (UnitType.CRUSADER_PALADIN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="crusader_pikeman",
        enemies=[
            (UnitType.CRUSADER_PIKEMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
    Battle(
        id="werebear",
        enemies=[
            (UnitType.WEREBEAR, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        ],
        dependencies=[],
        tip=["1"],
    ),
]

