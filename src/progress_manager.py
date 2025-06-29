"""Progress manager for the game."""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
from enum import Enum

from pydantic import BaseModel, ValidationError, field_serializer, field_validator
from platformdirs import user_config_dir

import battles
from components.unit_type import UnitType
from components.unit_tier import UnitTier
from corrupted_hexes import CorruptedHexes
from unit_values import unit_values
from hex_grid import hex_neighbors
from game_constants import gc
import random

# Current version of the progress manager
# Increment this when making breaking changes to save file format
CURRENT_VERSION = 1

class HexLifecycleState(Enum):
    """Enum representing the lifecycle state of a hex (battle or upgrade)."""
    FOGGED = "fogged"        # Not adjacent to any claimed hex, inaccessible
    UNCLAIMED = "unclaimed"  # Adjacent to claimed hex, accessible but never claimed/solved
    CLAIMED = "claimed"      # Claimed/solved once, never corrupted
    CORRUPTED = "corrupted"  # Claimed/solved once, then corrupted (can be claimed/solved again)
    RECLAIMED = "reclaimed"  # Claimed/solved twice (once normal, once corrupted)

def calculate_points_for_units(units: List[Tuple[UnitType, Tuple[float, float]]]) -> int:
    """Calculate total points for a list of unit placements."""
    return sum(unit_values[unit_type] for unit_type, _ in units)


def calculate_total_available_points() -> int:
    """Calculate total points available from starting units and completed battles."""
    points = sum(unit_values[unit_type] * count for unit_type, count in battles.starting_units.items())
    for battle in battles.get_battles():
        if battle.hex_coords in progress_manager.solutions:
            solution = progress_manager.solutions[battle.hex_coords]
            points += sum(unit_values[unit_type] for unit_type, _ in battle.enemies)
            points -= sum(unit_values[unit_type] for unit_type, _ in solution.unit_placements)
    return points


class Solution(BaseModel):
    hex_coords: Tuple[int, int]
    unit_placements: List[Tuple[UnitType, Tuple[float, float]]]
    solved_corrupted: bool

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
    game_completed_corruption: bool = False
    corrupted_hexes: CorruptedHexes = []  # Keep for battle compatibility
    unit_tiers: Dict[UnitType, UnitTier] = {}
    hex_states: Dict[Tuple[int, int], HexLifecycleState] = {}

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

    @field_serializer('unit_tiers')
    def serialize_unit_tiers(self, unit_tiers: Dict[UnitType, UnitTier]) -> Dict[str, str]:
        return {unit_type.value: tier.value for unit_type, tier in unit_tiers.items()}

    @field_validator('unit_tiers', mode='before')
    def parse_unit_tiers(cls, value: Any) -> Dict[UnitType, UnitTier]:
        if isinstance(value, dict):
            return {UnitType(unit_type): UnitTier(tier) for unit_type, tier in value.items()}
        return value

    @field_serializer('hex_states')
    def serialize_hex_states(self, hex_states: Dict[Tuple[int, int], HexLifecycleState]) -> Dict[str, str]:
        return {str(list(coords)): state.value for coords, state in hex_states.items()}

    @field_validator('hex_states', mode='before')
    def parse_hex_states(cls, value: Any) -> Dict[Tuple[int, int], HexLifecycleState]:
        if isinstance(value, dict):
            result = {}
            for key, state_value in value.items():
                coords = tuple(json.loads(key))
                result[coords] = HexLifecycleState(state_value)
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
        
        # Add all battles that have been solved already
        available_battles.extend([coords for coords in self.solutions if coords != (0, 0)])
        
        # If there are uncompleted corrupted battles, don't allow new battles to be unlocked
        if self.has_uncompleted_corrupted_battles():
            return available_battles
        
        # Otherwise, unlock adjacent battles normally
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
    
    def should_show_corruption_congratulations(self) -> bool:
        return all(
            battle.hex_coords in self.solutions and self.solutions[battle.hex_coords].solved_corrupted for battle in battles.get_battles()
            if not battle.is_test
        ) and not self.game_completed_corruption

    def mark_congratulations_shown(self) -> None:
        self.game_completed = True
        save_progress()

    def mark_corruption_congratulations_shown(self) -> None:
        self.game_completed_corruption = True
        save_progress()
        
    def should_trigger_corruption(self) -> bool:
        """Check if corruption should be triggered based on available unit points."""
        available_points = calculate_total_available_points()
        enough_points = available_points >= gc.CORRUPTION_TRIGGER_POINTS
        not_already_corrupted = not self.has_uncompleted_corrupted_battles()
        enough_uncorrupted_solved_battles = sum(
            1 for hex_coords in self.solutions.keys()
            if hex_coords not in self.corrupted_hexes
        ) >= gc.CORRUPTION_BATTLE_COUNT
        final_corruption = all(
            battle.hex_coords in self.solutions
            for battle in battles.get_battles()
            if not battle.is_test
        )
        all_levels_already_corrupted = all(
            battle.hex_coords in self.solutions and battle.hex_coords in self.corrupted_hexes
            for battle in battles.get_battles()
            if not battle.is_test
        )
        return (
            enough_points and
            not_already_corrupted and
            (enough_uncorrupted_solved_battles or final_corruption)
        ) and not all_levels_already_corrupted

    def corrupt_battles(self) -> List[Tuple[int, int]]:
        """Corrupt a number of completed battles and claimed upgrade hexes based on the game constants."""
        import upgrade_hexes
        
        # Include completed battles that aren't corrupted yet
        completed_battles = [coord for coord in self.solutions 
                            if coord not in self.corrupted_hexes]
        
        # Include upgrade hexes that are in CLAIMED state (can be corrupted)
        corruptible_upgrade_hexes = [coord for coord, state in self.hex_states.items()
                                   if upgrade_hexes.is_upgrade_hex(coord) and state == HexLifecycleState.CLAIMED]
        
        corruption_pool = completed_battles + corruptible_upgrade_hexes
        
        if not corruption_pool:
            return []
        num_corruptions = min(gc.CORRUPTION_BATTLE_COUNT, len(corruption_pool))
        hexes_to_corrupt = random.sample(corruption_pool, num_corruptions)
        
        # Update states and corrupted_hexes list
        for coords in hexes_to_corrupt:
            if upgrade_hexes.is_upgrade_hex(coords):
                # Change upgrade hex from CLAIMED to CORRUPTED
                self.set_hex_state(coords, HexLifecycleState.CORRUPTED)
            else:
                # Add battle to corrupted_hexes list (keeping old system for battles)
                self.corrupted_hexes.append(coords)
        
        save_progress()
        return hexes_to_corrupt
        
    def is_battle_corrupted(self, hex_coords: Tuple[int, int]) -> bool:
        """Check if a battle is corrupted."""
        return hex_coords in self.corrupted_hexes
        
    def has_uncompleted_corrupted_battles(self) -> bool:
        """Check if there are any corrupted battles or upgrade hexes that need to be cleared."""
        import upgrade_hexes
        
        # Check for corrupted battles (using old system)
        for coords in self.corrupted_hexes:
            if not self.has_solved_corrupted_battle(coords):
                return True
        
        # Check for corrupted upgrade hexes (using new lifecycle system)
        for coords, state in self.hex_states.items():
            if upgrade_hexes.is_upgrade_hex(coords) and state == HexLifecycleState.CORRUPTED:
                return True
        
        return False

    def has_solved_corrupted_battle(self, hex_coords: Tuple[int, int]) -> bool:
        """Check if a battle has been solved in its corrupted state."""
        return (hex_coords in self.solutions and 
                hex_coords in self.corrupted_hexes and 
                self.solutions[hex_coords].solved_corrupted)

    def get_unit_tier(self, unit_type: UnitType) -> UnitTier:
        """Get the current tier of a unit type."""
        return self.unit_tiers.get(unit_type, UnitTier.BASIC)

    def can_upgrade_unit(self, unit_type: UnitType) -> bool:
        """Check if a unit can be upgraded to the next tier."""
        current_tier = self.get_unit_tier(unit_type)
        available_advanced, available_elite = self.calculate_available_credits()
        
        if current_tier == UnitTier.BASIC:
            return available_advanced > 0
        elif current_tier == UnitTier.ADVANCED:
            return available_elite > 0
        return False

    def upgrade_unit(self, unit_type: UnitType) -> bool:
        """Upgrade a unit to the next tier. Returns True if successful."""
        current_tier = self.get_unit_tier(unit_type)
        available_advanced, available_elite = self.calculate_available_credits()
        
        if current_tier == UnitTier.BASIC and available_advanced > 0:
            self.unit_tiers[unit_type] = UnitTier.ADVANCED
            save_progress()
            return True
        elif current_tier == UnitTier.ADVANCED and available_elite > 0:
            self.unit_tiers[unit_type] = UnitTier.ELITE
            save_progress()
            return True
        
        return False

    def get_hex_state(self, hex_coords: Tuple[int, int]) -> HexLifecycleState:
        """Get the current lifecycle state of a hex."""
        return self.hex_states.get(hex_coords, HexLifecycleState.FOGGED)

    def set_hex_state(self, hex_coords: Tuple[int, int], state: HexLifecycleState) -> None:
        """Set the lifecycle state of a hex."""
        if state == HexLifecycleState.FOGGED:
            # Remove from dict if fogged (default state)
            self.hex_states.pop(hex_coords, None)
        else:
            self.hex_states[hex_coords] = state
        save_progress()

    def is_upgrade_hex_accessible(self, hex_coords: Tuple[int, int]) -> bool:
        """Check if an upgrade hex is accessible (adjacent to a claimed hex)."""
        import upgrade_hexes
        
        if not upgrade_hexes.is_upgrade_hex(hex_coords):
            return False
            
        # Check if adjacent to any claimed upgrade hex or solved battle
        for neighbor_coords in hex_neighbors(hex_coords):
            # Check if neighbor is a solved battle
            if neighbor_coords in self.solutions:
                return True
            # Check if neighbor is a claimed upgrade hex (any state except FOGGED)
            neighbor_state = self.get_hex_state(neighbor_coords)
            if upgrade_hexes.is_upgrade_hex(neighbor_coords) and neighbor_state != HexLifecycleState.FOGGED:
                return True
        
        return False

    def get_effective_hex_state(self, hex_coords: Tuple[int, int]) -> HexLifecycleState:
        """Get the effective state of a hex, considering accessibility for upgrade hexes."""
        import upgrade_hexes
        
        stored_state = self.get_hex_state(hex_coords)
        
        # For upgrade hexes, check if they should be accessible
        if upgrade_hexes.is_upgrade_hex(hex_coords):
            if stored_state == HexLifecycleState.FOGGED:
                # If fogged, check if it should become accessible
                if self.is_upgrade_hex_accessible(hex_coords):
                    return HexLifecycleState.UNCLAIMED
                else:
                    return HexLifecycleState.FOGGED
        
        return stored_state



    def is_upgrade_hex_claimable(self, hex_coords: Tuple[int, int]) -> bool:
        """Check if an upgrade hex can be claimed."""
        state = self.get_effective_hex_state(hex_coords)
        return state == HexLifecycleState.UNCLAIMED or state == HexLifecycleState.CORRUPTED

    def claim_upgrade_hex(self, hex_coords: Tuple[int, int]) -> bool:
        """Claim an upgrade hex. Returns True if successful."""
        current_state = self.get_effective_hex_state(hex_coords)
        
        if current_state == HexLifecycleState.UNCLAIMED:
            # First claim - goes to CLAIMED state
            self.set_hex_state(hex_coords, HexLifecycleState.CLAIMED)
            return True
        elif current_state == HexLifecycleState.CORRUPTED:
            # Second claim (after corruption) - goes to RECLAIMED state
            self.set_hex_state(hex_coords, HexLifecycleState.RECLAIMED)
            return True
        
        return False  # Already claimed or reclaimed

    def calculate_available_credits(self) -> Tuple[int, int]:
        """Calculate available advanced and elite credits based on hex lifecycle states minus upgraded units."""
        import upgrade_hexes
        
        # Count upgraded units by tier
        advanced_upgrades = sum(1 for tier in self.unit_tiers.values() if tier == UnitTier.ADVANCED)
        elite_upgrades = sum(1 for tier in self.unit_tiers.values() if tier == UnitTier.ELITE)
        
        # Count upgrade hexes by their lifecycle state
        advanced_credits_earned = 0
        elite_credits_earned = 0
        
        for coords, state in self.hex_states.items():
            if upgrade_hexes.is_upgrade_hex(coords):
                if state in [HexLifecycleState.CLAIMED, HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]:
                    advanced_credits_earned += 1  # First claim gives advanced credit
                if state == HexLifecycleState.RECLAIMED:
                    elite_credits_earned += 1  # Second claim (after corruption) gives elite credit
        
        # Calculate available credits
        available_advanced = max(0, advanced_credits_earned - advanced_upgrades - elite_upgrades)
        available_elite = max(0, elite_credits_earned - elite_upgrades)
        
        return available_advanced, available_elite

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
            try:
                save_data = json.load(file)
            except json.JSONDecodeError:
                print("Error loading save data, creating new save")
                new_progress = ProgressManager()
            else:
                try:
                    new_progress = ProgressManager.model_validate(save_data)
                except ValidationError:
                    print("Error validating save data, creating new save")
                    new_progress = ProgressManager()
                else:
                    if not is_save_compatible(save_data):
                        print("Save data is out of date, creating new save")
                        new_progress = ProgressManager()
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
    progress_manager.corrupted_hexes = []
    progress_manager.unit_tiers = {}
    progress_manager.hex_states = {}
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
