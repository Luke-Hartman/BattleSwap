"""Module for handling battles in the game using Pydantic models.

This module defines the Battle model and loads battle data from a JSON file.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import BaseModel

from entities.units import UnitType

starting_units: Dict[UnitType, int] = {
    UnitType.CORE_SWORDSMAN: 3,
    UnitType.CORE_ARCHER: 3,
    UnitType.CORE_HORSEMAN: 3,
    # UnitType.CRUSADER_CLERIC: 2,
    # UnitType.CRUSADER_DEFENDER: 3,
    # UnitType.CRUSADER_LONGBOWMAN: 2,
    # UnitType.CRUSADER_PIKEMAN: 3,
    # UnitType.CRUSADER_PALADIN: 3,
    UnitType.CRUSADER_RED_KNIGHT: 3,
    UnitType.CRUSADER_GOLD_KNIGHT: 3,
    UnitType.CRUSADER_COMMANDER: 1,
    UnitType.CRUSADER_BLACK_KNIGHT: 3,
    # UnitType.CORE_MAGE: 2,
}

class Battle(BaseModel):
    """Data model for a battle."""
    id: str
    enemies: List[Tuple[UnitType, Tuple[int, int]]]
    dependencies: List[str]
    tip: List[str]

def get_battle(battle_id: str) -> Battle:
    """Retrieve a battle by its ID."""
    for battle in battles:
        if battle.id == battle_id:
            return battle
    raise ValueError(f"Battle with id {battle_id} not found")

battles: List[Battle] = []

def reload_battles() -> None:
    """Load battles from a JSON file."""
    file_path = Path(__file__).parent.parent / 'data' / 'battles.json'
    with open(file_path, 'r') as file:
        battles_data = json.load(file)
        global battles
        battles = [Battle.model_validate(battle) for battle in battles_data]

reload_battles()

