"""The data for the levels in the game."""

from dataclasses import dataclass
from typing import List, Tuple
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, NO_MANS_LAND_WIDTH
from entities.units import UnitType

starting_units = {
    UnitType.CORE_SWORDSMAN: 3,
    UnitType.CORE_ARCHER: 3,
    UnitType.CORE_HORSEMAN: 3,
    # UnitType.CRUSADER_CLERIC: 2,
    # UnitType.CRUSADER_DEFENDER: 3,
    # UnitType.CRUSADER_LONGBOWMAN: 2,
    # UnitType.CRUSADER_PIKEMAN: 3,
    # UnitType.CRUSADER_PALADIN: 3,
    # UnitType.CRUSADER_RED_KNIGHT: 3,
    # UnitType.CORE_MAGE: 2,
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
        id="crusaders_1",
        enemies=[ # 4 defenders, 5 pikemen behind them (pikemen are between the defenders, but back a bit)
            (UnitType.CRUSADER_DEFENDER, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 + 100)),
            (UnitType.CRUSADER_DEFENDER, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 + 0)),
            (UnitType.CRUSADER_DEFENDER, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 - 100)),
            (UnitType.CRUSADER_LONGBOWMAN, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2 + 50, BATTLEFIELD_HEIGHT // 2 + 250)),
            (UnitType.CRUSADER_LONGBOWMAN, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2 + 50, BATTLEFIELD_HEIGHT // 2 - 250)),
        ],
        dependencies=[],
        tip=[
            "TODO",
        ]
    ),
    Battle(
        id="crusaders_2",
        enemies=[
            (UnitType.CRUSADER_PIKEMAN, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 + 100)),
            (UnitType.CRUSADER_PIKEMAN, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CRUSADER_PIKEMAN, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 - 100)),
            (UnitType.CRUSADER_CLERIC, (BATTLEFIELD_WIDTH * 3 // 4 + 125, BATTLEFIELD_HEIGHT // 2 + 75)),
            (UnitType.CRUSADER_CLERIC, (BATTLEFIELD_WIDTH * 3 // 4 + 125, BATTLEFIELD_HEIGHT // 2 - 75)),
        ],
        dependencies=[],
        tip=[
            "TODO",
        ]
    ),
    Battle(
        id="crusaders_3",
        enemies=[
            (UnitType.CRUSADER_PALADIN, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 + 200)),
            (UnitType.CRUSADER_PALADIN, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 + 0)),
            (UnitType.CRUSADER_PALADIN, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 - 200)),
        ],
        dependencies=[],
        tip=["blahg"],
    ),
    Battle(
        id="crusaders_4",
        enemies=[
            (UnitType.CRUSADER_DEFENDER, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 + 100)),
            (UnitType.CRUSADER_DEFENDER, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2)),
            (UnitType.CRUSADER_DEFENDER, (BATTLEFIELD_WIDTH * 3 // 4, BATTLEFIELD_HEIGHT // 2 - 100)),
            (UnitType.CRUSADER_PIKEMAN, (BATTLEFIELD_WIDTH * 3 // 4 + 50, BATTLEFIELD_HEIGHT // 2 + 50)),
            (UnitType.CRUSADER_PIKEMAN, (BATTLEFIELD_WIDTH * 3 // 4 + 50, BATTLEFIELD_HEIGHT // 2 - 50)),
            (UnitType.CRUSADER_LONGBOWMAN, (BATTLEFIELD_WIDTH * 3 // 4 + 100, BATTLEFIELD_HEIGHT // 2 + 250)),
            (UnitType.CRUSADER_LONGBOWMAN, (BATTLEFIELD_WIDTH * 3 // 4 + 100, BATTLEFIELD_HEIGHT // 2 - 250)),
        ],
        dependencies=[],
        tip=["asdf"],
    )
]

