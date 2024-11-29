"""Module for handling battles in the game using Pydantic models.

This module defines the Battle model and loads battle data from a JSON file.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from entities.units import UnitType

starting_units: Dict[UnitType, int] = {
    UnitType.CORE_DUELIST: 1
}

class Battle(BaseModel):
    """A battle configuration."""
    id: str
    enemies: List[Tuple[UnitType, Tuple[int, int]]]
    allies: Optional[List[Tuple[UnitType, Tuple[int, int]]]]
    tip: List[str]
    dependencies: List[str]
    is_test: bool
    tip_voice_filename: Optional[str]

def get_battle(battle_id: str) -> Battle:
    """Retrieve a battle by its ID."""
    for battle in _battles:
        if battle.id == battle_id:
            return battle
    raise ValueError(f"Battle with id {battle_id} not found")

def get_battles() -> List[Battle]:
    """Get all battles."""
    return _battles.copy()

_battles: List[Battle] = []

def _validate_battles(battles: List[Battle]) -> None:
    """Validate the battles list."""
    for battle in battles:
        for dependency in battle.dependencies:
            assert any(dep.id == dependency for dep in battles)
    # all names are unique
    if len(battles) != len(set(battle.id for battle in battles)):
        duplicates = [id for id in set(battle.id for battle in battles) if list(battle.id for battle in battles).count(id) > 1]
        raise ValueError(f"Duplicate battle ids: {duplicates}")
    # battles do not have allies unless they are tests
    for battle in battles:
        if not battle.is_test and battle.allies is not None:
            raise ValueError(f"Battle {battle.id} has allies but is not a test")


def reload_battles() -> None:
    """Load battles from a JSON file."""
    file_path = Path(__file__).parent.parent / 'data' / 'battles.json'
    with open(file_path, 'r') as file:
        battles_data = json.load(file)
        global _battles
        _battles = [Battle.model_validate(battle) for battle in battles_data]
        _validate_battles(_battles)

reload_battles()

def move_battle_to_top(battle_id: str) -> None:
    """Move a battle to the top of the list."""
    battle = get_battle(battle_id)
    _battles.remove(battle)
    _battles.insert(0, battle)
    _save_battles(_battles)

def move_battle_up(battle_id: str) -> None:
    """Move a battle up one position."""
    for i, battle in enumerate(_battles):
        if battle.id == battle_id and i > 0:
            _battles[i], _battles[i-1] = _battles[i-1], _battles[i]
            _save_battles(_battles)
            break

def move_battle_down(battle_id: str) -> None:
    """Move a battle down one position."""
    for i, battle in enumerate(_battles):
        if battle.id == battle_id and i < len(_battles) - 1:
            _battles[i], _battles[i+1] = _battles[i+1], _battles[i]
            _save_battles(_battles)
            break

def move_battle_to_bottom(battle_id: str) -> None:
    """Move a battle to the bottom of the list."""
    battle = get_battle(battle_id)
    _battles.remove(battle)
    _battles.append(battle)
    _save_battles(_battles)

def _save_battles(battles: List[Battle]) -> None:
    """Save the current battles list to the JSON file."""
    _validate_battles(battles)
    file_path = Path(__file__).parent.parent / 'data' / 'battles.json'
    battles_data = [battle.model_dump() for battle in battles]
    with open(file_path, 'w') as file:
        json.dump(battles_data, file, indent=2)
    reload_battles()

def move_battle_after(battle_id: str, target_battle_id: str) -> None:
    """Move a battle to the position immediately after the target battle."""
    battle = get_battle(battle_id)
    target_index = next(i for i, b in enumerate(_battles) if b.id == target_battle_id)
    
    # Remove the battle from its current position
    _battles.remove(battle)
    
    # Insert it after the target battle
    _battles.insert(target_index + 1, battle)
    _save_battles(_battles)

def depend_on_previous_battle(battle_id: str) -> None:
    """Add a dependency to the previous battle."""
    for i, battle in enumerate(_battles):
        if battle.id == battle_id:
            assert i > 0
            battle.dependencies.append(_battles[i - 1].id)
            _save_battles(_battles)
            return
    raise ValueError(f"Battle with id {battle_id} not found")

def add_battle(battle: Battle) -> None:
    """Add a battle to the list."""
    _battles.append(battle)
    _save_battles(_battles)

def update_battle(previous_battle: Battle, updated_battle: Battle) -> None:
    """Update a battle in the list and save changes."""
    if previous_battle.id == updated_battle.id:
        for i, battle in enumerate(_battles):
            if battle.id == updated_battle.id:
                _battles[i] = updated_battle
    else:
        for i, battle in enumerate(_battles):
            if battle.id == previous_battle.id:
                _battles[i] = updated_battle
            else:
                if previous_battle.id in _battles[i].dependencies:
                    _battles[i].dependencies.remove(previous_battle.id)
                    _battles[i].dependencies.append(updated_battle.id)
    _save_battles(_battles)

def delete_battle(battle_id: str) -> None:
    """Delete a battle from the list."""
    battle = get_battle(battle_id)
    _battles.remove(battle)
    for i, b in enumerate(_battles):
        if battle_id in b.dependencies:
            b.dependencies.remove(battle_id)
    _save_battles(_battles)

