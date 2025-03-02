"""Progress manager for the game."""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

from pydantic import BaseModel, field_serializer, field_validator
from platformdirs import user_config_dir

import battles
from components.unit_type import UnitType
from unit_values import unit_values
from hex_grid import hex_neighbors

# Current version of the progress manager
# Increment this when making breaking changes to save file format
CURRENT_VERSION = 1

def calculate_points_for_units(units: List[Tuple[UnitType, Tuple[float, float]]]) -> int:
    """Calculate total points for a list of unit placements."""
    return sum(unit_values[unit_type] for unit_type, _ in units)


def calculate_total_available_points() -> int:
    """Calculate total points available from starting units and completed battles."""
    points = sum(unit_values[unit_type] * count for unit_type, count in battles.starting_units.items())
    for battle in battles.get_battles():
        if battle.hex_coords in progress_manager.solutions:
            points += sum(unit_values[unit_type] for unit_type, _ in battle.enemies)
    return points


class Solution(BaseModel):
    hex_coords: Tuple[int, int]
    unit_placements: List[Tuple[UnitType, Tuple[float, float]]]

    @field_serializer('hex_coords')
    def serialize_hex_coords(self, hex_coords: Tuple[int, int]) -> List[int]:
        return list(hex_coords)

    @field_validator('hex_coords', mode='before')
    def parse_hex_coords(cls, value: Any) -> Tuple[int, int]:
        if isinstance(value, list):
            return tuple(value)
        return value

    @field_serializer('unit_placements')
    def serialize_unit_placements(self, unit_placements: List[Tuple[UnitType, Tuple[float, float]]]) -> List[List[Any]]:
        return [[unit_type.value, list(coords)] for unit_type, coords in unit_placements]

    @field_validator('unit_placements', mode='before')
    def parse_unit_placements(cls, value: Any) -> List[Tuple[UnitType, Tuple[float, float]]]:
        if isinstance(value, list) and all(isinstance(x, list) for x in value):
            return [(UnitType(unit_type), tuple(coords)) for unit_type, coords in value]
        return value


class ProgressManager(BaseModel):
    version: int = CURRENT_VERSION
    solutions: Dict[Tuple[int, int], Solution] = {}
    game_completed: bool = False

    @field_serializer('solutions')
    def serialize_solutions(self, solutions: Dict[Tuple[int, int], Solution]) -> Dict[str, Any]:
        return {str(list(coords)): solution.model_dump() for coords, solution in solutions.items()}

    @field_validator('solutions', mode='before')
    def parse_solutions(cls, value: Any) -> Dict[Tuple[int, int], Solution]:
        if isinstance(value, dict):
            result = {}
            for key, solution_data in value.items():
                coords = tuple(json.loads(key))
                result[coords] = Solution.model_validate(solution_data)
            return result
        return value

    def calculate_battle_grade(self, battle: battles.Battle) -> Optional[str]:
        """Calculate grade for a specific battle based on units used."""
        if not battle.grades or battle.hex_coords not in self.solutions:
            return None
        solution = self.solutions[battle.hex_coords]
        points_used = calculate_points_for_units(solution.unit_placements)
        return battle.grades.get_grade(points_used)
    
    def calculate_overall_grade(self) -> str:
        """Calculate overall grade based on total points used across all completed battles."""
        points_used = 0
        total_a_cutoff = 0
        total_b_cutoff = 0
        total_c_cutoff = 0
        total_d_cutoff = 0
        
        for battle in battles.get_battles():
            if not battle.grades or battle.hex_coords not in self.solutions:
                continue
            solution = self.solutions[battle.hex_coords]
            points_used += calculate_points_for_units(solution.unit_placements)
            total_a_cutoff += battle.grades.a_cutoff
            total_b_cutoff += battle.grades.b_cutoff
            total_c_cutoff += battle.grades.c_cutoff
            total_d_cutoff += battle.grades.d_cutoff
            
        # If no battles completed yet, return "-"
        if total_d_cutoff == 0:
            return "-"
            
        if points_used <= total_a_cutoff:
            return 'A'
        elif points_used <= total_b_cutoff:
            return 'B'
        elif points_used <= total_c_cutoff:
            return 'C'
        elif points_used <= total_d_cutoff:
            return 'D'
        return 'F'

    def get_overall_grade_cutoffs(self) -> Dict[str, int]:
        """Get the total grade cutoffs across all completed battles."""
        total_cutoffs = defaultdict(int)
        for battle in battles.get_battles():
            if battle.grades and battle.hex_coords in self.solutions:
                total_cutoffs['a'] += battle.grades.a_cutoff
                total_cutoffs['b'] += battle.grades.b_cutoff
                total_cutoffs['c'] += battle.grades.c_cutoff
                total_cutoffs['d'] += battle.grades.d_cutoff
        return dict(total_cutoffs)

    def available_units(self, current_battle: Optional[battles.Battle]) -> Dict[UnitType, int]:
        """Get the available units for the player."""
        units = defaultdict(int)
        units.update(battles.starting_units)
        # Handle units from battles other than the current one
        for coords in self.solutions:
            if current_battle is not None and current_battle.hex_coords == coords:
                continue
            battle = battles.get_battle_coords(coords)
            for (unit_type, _) in battle.enemies:
                units[unit_type] += 1
            for (unit_type, _) in self.solutions[coords].unit_placements:
                units[unit_type] -= 1
        # Handle units from the current battle
        if current_battle is not None and current_battle.allies is not None:
            if current_battle.hex_coords in self.solutions:
                for (unit_type, _) in current_battle.enemies:
                    units[unit_type] += 1
            for (unit_type, _) in current_battle.allies:
                units[unit_type] -= 1
        for unit_type, count in units.items():
            assert count >= 0, str(units)
        return units

    def available_battles(self) -> List[Tuple[int, int]]:
        """Get the available battles for the player."""
        available_battles = [(0, 0)]  # 0, 0 is always available
        progress = True
        while progress:
            progress = False
            for battle in battles.get_battles():
                coords = battle.hex_coords
                if (
                    coords not in available_battles
                    and not battle.is_test
                    and any(neighbor in self.solutions for neighbor in hex_neighbors(coords))
                ):
                    available_battles.append(coords)
                    progress = True
        return available_battles

    def get_battles_including_solutions(self) -> List[battles.Battle]:
        """Get all battles, and include ally positions for solved battles."""
        all_battles = battles.get_battles()
        for battle in all_battles:
            if battle.hex_coords in self.solutions:
                battle.allies = self.solutions[battle.hex_coords].unit_placements
        return all_battles

    def save_solution(self, solution: Solution) -> None:
        """Save a solution."""
        self.solutions[solution.hex_coords] = solution
        save_progress()

    def should_show_congratulations(self) -> bool:
        return all(
            battle.hex_coords in self.solutions for battle in battles.get_battles()
            if not battle.is_test
        ) and not self.game_completed

    def mark_congratulations_shown(self) -> None:
        self.game_completed = True
        save_progress()

def get_progress_path() -> Path:
    """Get the path to the progress file."""
    progress_dir = Path(user_config_dir("battleswap"))
    progress_dir.mkdir(parents=True, exist_ok=True)
    return progress_dir / "progress.json"


progress_manager: Optional[ProgressManager] = None


def save_progress() -> None:
    """Save the progress to the JSON file."""
    global progress_manager
    if progress_manager is None:
        return
    
    progress_path = get_progress_path()
    with open(progress_path, "w") as file:
        json.dump(progress_manager.model_dump(), file, indent=4)


def is_save_compatible(save_data: dict) -> bool:
    """Check if the save file is compatible with current version.
    
    Returns:
        bool: True if the save is compatible, False otherwise.
    """
    return save_data.get('version', 0) == CURRENT_VERSION


def load_progress() -> None:
    """Load the progress from the JSON file or create default progress if the file doesn't exist."""
    global progress_manager
    progress_path = get_progress_path()
    
    if progress_path.exists():
        with open(progress_path, "r") as file:
            save_data = json.load(file)
            if not is_save_compatible(save_data):
                # Create new progress if version is incompatible
                new_progress = ProgressManager()
            else:
                new_progress = ProgressManager.model_validate(save_data)
    else:
        new_progress = ProgressManager()
        # Save default progress
        with open(progress_path, "w") as file:
            json.dump(new_progress.model_dump(), file, indent=4)
    
    if progress_manager is None:
        progress_manager = new_progress
    else:
        for field in progress_manager.model_fields:
            setattr(progress_manager, field, getattr(new_progress, field))

def reset_progress() -> None:
    """Reset the progress."""
    global progress_manager
    progress_manager.solutions = {}
    save_progress()

def has_incompatible_save() -> bool:
    """Check if there is an incompatible save file.
    
    Returns:
        bool: True if there is an incompatible save file, False otherwise.
    """
    progress_path = get_progress_path()
    if not progress_path.exists():
        return False
        
    try:
        with open(progress_path, "r") as file:
            save_data = json.load(file)
            return not is_save_compatible(save_data)
    except (json.JSONDecodeError, IOError):
        return False

# Initialize progress on module import
load_progress()
