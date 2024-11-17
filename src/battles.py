"""Module for handling battles in the game using Pydantic models.

This module defines the Battle model and loads battle data from a JSON file.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import BaseModel

from entities.units import UnitType

starting_units: Dict[UnitType, int] = {
    UnitType.CORE_ARCHER: 5,
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

def move_battle_to_top(battle_id: str) -> None:
    """Move a battle to the top of the list."""
    battle = get_battle(battle_id)
    battles.remove(battle)
    battles.insert(0, battle)
    _save_battles()

def move_battle_up(battle_id: str) -> None:
    """Move a battle up one position."""
    for i, battle in enumerate(battles):
        if battle.id == battle_id and i > 0:
            battles[i], battles[i-1] = battles[i-1], battles[i]
            _save_battles()
            break

def move_battle_down(battle_id: str) -> None:
    """Move a battle down one position."""
    for i, battle in enumerate(battles):
        if battle.id == battle_id and i < len(battles) - 1:
            battles[i], battles[i+1] = battles[i+1], battles[i]
            _save_battles()
            break

def move_battle_to_bottom(battle_id: str) -> None:
    """Move a battle to the bottom of the list."""
    battle = get_battle(battle_id)
    battles.remove(battle)
    battles.append(battle)
    _save_battles()

def _save_battles() -> None:
    """Save the current battles list to the JSON file."""
    file_path = Path(__file__).parent.parent / 'data' / 'battles.json'
    battles_data = [battle.model_dump() for battle in battles]
    with open(file_path, 'w') as file:
        json.dump(battles_data, file, indent=2)
    reload_battles()

