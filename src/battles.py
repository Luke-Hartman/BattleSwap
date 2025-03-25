"""Module for handling battles in the game using Pydantic models.

This module defines the Battle model and loads battle data from a JSON file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel
from unit_values import unit_values
from entities.units import UnitType
from corruption_powers import CorruptionPowerUnion

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return Path(base_path) / relative_path

starting_units: Dict[UnitType, int] = {
    UnitType.CORE_DUELIST: 1
}

class BattleGrades(BaseModel):
    """Grade cutoffs for a battle."""
    a_cutoff: int
    b_cutoff: int
    c_cutoff: int
    d_cutoff: int

    def get_grade(self, points_used: int) -> str:
        """Get the grade for a given number of points used."""
        if points_used <= self.a_cutoff:
            return 'A'
        elif points_used <= self.b_cutoff:
            return 'B'
        elif points_used <= self.c_cutoff:
            return 'C'
        elif points_used <= self.d_cutoff:
            return 'D'
        return 'F'

class Battle(BaseModel):
    """A battle configuration."""
    id: str
    enemies: List[Tuple[UnitType, Tuple[float, float]]]
    allies: Optional[List[Tuple[UnitType, Tuple[float, float]]]]
    tip: List[str]
    hex_coords: Optional[Tuple[int, int]]
    is_test: bool
    tip_voice_filename: Optional[str] = None
    grades: Optional[BattleGrades] = None
    best_solution: Optional[List[Tuple[UnitType, Tuple[float, float]]]] = None
    best_corrupted_solution: Optional[List[Tuple[UnitType, Tuple[float, float]]]] = None
    corruption_powers: Optional[List[CorruptionPowerUnion]] = None

def get_battle_id(battle_id: str) -> Battle:
    """Retrieve a battle by its ID."""
    for battle in _battles:
        if battle.id == battle_id:
            return battle
    raise ValueError(f"Battle with id {battle_id} not found")

def get_battle_coords(battle_coords: Tuple[int, int]) -> Battle:
    """Retrieve a battle by its coordinates."""
    for battle in _battles:
        if battle.hex_coords == battle_coords:
            return battle
    raise ValueError(f"Battle with coords {battle_coords} not found")

def get_battles() -> List[Battle]:
    """Get all battles."""
    return [battle.model_copy(deep=True) for battle in _battles]

_battles: List[Battle] = []

def reload_battles() -> None:
    """Load battles from a JSON file."""
    file_path = get_resource_path('data/battles.json')
    with open(file_path, 'r') as file:
        battles_data = json.load(file)
        global _battles
        _battles = [Battle.model_validate(battle) for battle in battles_data]

reload_battles()

def move_battle_to_top(battle_id: str) -> None:
    """Move a battle to the top of the list."""
    battle = get_battle_id(battle_id)
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
    battle = get_battle_id(battle_id)
    _battles.remove(battle)
    _battles.append(battle)
    _save_battles(_battles)

def _save_battles(battles: List[Battle]) -> None:
    """Save the current battles list to the JSON file."""
    file_path = get_resource_path('data/battles.json')
    battles_data = [battle.model_dump() for battle in battles]
    
    # If two battles have the same id or hex_coords (excluding None), raise an error
    for i, battle in enumerate(battles_data):
        for other_battle in battles_data[i + 1:]:
            if battle['id'] == other_battle['id']:
                raise ValueError(f"Duplicate battle id: {battle}")
            if (
                battle['hex_coords'] is not None 
                and battle['hex_coords'] == other_battle['hex_coords']
            ):
                raise ValueError(
                    f"Duplicate battle hex_coords. Battle1: {battle}, Battle2: {other_battle}"
                )
    
    with open(file_path, 'w') as file:
        json.dump(battles_data, file, indent=2)
    reload_battles()

def move_battle_after(battle_id: str, target_battle_id: str) -> None:
    """Move a battle to the position immediately after the target battle."""
    battle = get_battle_id(battle_id)
    target_index = next(i for i, b in enumerate(_battles) if b.id == target_battle_id)
    
    # Remove the battle from its current position
    _battles.remove(battle)
    
    # Insert it after the target battle
    _battles.insert(target_index + 1, battle)
    _save_battles(_battles)

def add_battle(battle: Battle) -> None:
    """Add a battle to the list."""
    _battles.append(battle)
    _save_battles(_battles)

def update_battle(previous_battle: Battle, updated_battle: Battle) -> None:
    """Update a battle in the list and save changes."""
    # Find the battle to update
    target_battle = None
    target_index = -1
    
    for i, battle in enumerate(_battles):
        if battle.id == previous_battle.id:
            target_battle = battle
            target_index = i
            break
    
    if target_battle is None:
        raise ValueError(f"Battle with id {previous_battle.id} not found")
    
    # Preserve existing best solutions if not provided in the updated battle
    if updated_battle.best_solution is None:
        updated_battle.best_solution = target_battle.best_solution

    if updated_battle.best_corrupted_solution is None:
        updated_battle.best_corrupted_solution = target_battle.best_corrupted_solution

    # If existing battle doesn't have solutions, use the updated battle's solutions
    if target_battle.best_solution is None:
        target_battle.best_solution = updated_battle.best_solution
        
    if target_battle.best_corrupted_solution is None:
        target_battle.best_corrupted_solution = updated_battle.best_corrupted_solution
    
    # Update the battle
    if previous_battle.id == updated_battle.id:
        _battles[target_index] = updated_battle
    else:
        _battles[target_index] = updated_battle
    
    _save_battles(_battles)

def delete_battle(battle_id: str) -> None:
    """Delete a battle from the list."""
    battle = get_battle_id(battle_id)
    _battles.remove(battle)
    _save_battles(_battles)

