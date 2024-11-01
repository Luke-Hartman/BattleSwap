"""The data for the levels in the game."""

from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, NO_MANS_LAND_WIDTH
from entities.units import UnitType

starting_units = {
    UnitType.ARCHER: 5,
}

enemies = {
    "tutorial_1": [
        (UnitType.HORSEMAN, ((BATTLEFIELD_WIDTH * 3 // 4) + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
    ],
    "tutorial_2": [
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT * 1 // 8)),
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT * 7 // 8)),
    ],
    "tutorial_3": [
        (UnitType.FANCY_SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
    ],
    "tutorial_4": [
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 0 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 2 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 3 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        (UnitType.SWORDSMAN, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 4 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2)),
        (UnitType.ARCHER, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 + BATTLEFIELD_HEIGHT // 4)),
        (UnitType.ARCHER, (BATTLEFIELD_WIDTH // 2 + BATTLEFIELD_WIDTH * 1 // 10 + NO_MANS_LAND_WIDTH // 2, BATTLEFIELD_HEIGHT // 2 - BATTLEFIELD_HEIGHT // 4)),
    ],
}

dependencies = {
    "tutorial_1": [],
    "tutorial_2": ["tutorial_1"],
    "tutorial_3": ["tutorial_2"],
    "tutorial_4": ["tutorial_3"],
}