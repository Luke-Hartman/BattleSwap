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
from unit_values import unit_values
from hex_grid import hex_neighbors
from game_constants import gc
import random

# Current version of the progress manager
# Increment this when making breaking changes to save file format
CURRENT_VERSION = 2

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
        self.claim_hex(solution.hex_coords)
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
        not_already_corrupted = not any(
            state in [HexLifecycleState.CORRUPTED]
            for state in self.hex_states.values()
        )
        enough_claimed_hexes = sum(
            1 for hex_coords in self.hex_states if self.hex_states[hex_coords] == HexLifecycleState.CLAIMED
        ) >= gc.CORRUPTION_BATTLE_COUNT
        final_corruption = all(
            state in [HexLifecycleState.CLAIMED, HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]
            for state in self.hex_states.values()
        )
        all_levels_already_corrupted = all(
            state in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]
            for state in self.hex_states.values()
        )
        return (
            enough_points and
            not_already_corrupted and
            (enough_claimed_hexes or final_corruption)
        ) and not all_levels_already_corrupted

    def corrupt_battles(self) -> List[Tuple[int, int]]:
        """Corrupt a number of completed battles and claimed upgrade hexes based on the game constants."""
        import upgrade_hexes
        
        # Include completed battles that aren't corrupted yet
        corruption_pool = [coord for coord in self.hex_states if self.hex_states[coord] == HexLifecycleState.CLAIMED]
        
        if not corruption_pool:
            return []
        num_corruptions = min(gc.CORRUPTION_BATTLE_COUNT, len(corruption_pool))
        hexes_to_corrupt = random.sample(corruption_pool, num_corruptions)
        
        # Update states - corrupt claimed hexes and fog unclaimed hexes
        for coords in hexes_to_corrupt:
            self.set_hex_state(coords, HexLifecycleState.CORRUPTED)
        
        # Fog all unclaimed hexes to prevent new claims during corruption
        unclaimed_hexes = [coord for coord in self.hex_states if self.hex_states[coord] == HexLifecycleState.UNCLAIMED]
        for coords in unclaimed_hexes:
            self.set_hex_state(coords, HexLifecycleState.FOGGED)
        
        save_progress()
        return hexes_to_corrupt
        
    def has_uncompleted_corrupted_battles(self) -> bool:
        """Check if there are any corrupted battles or upgrade hexes that need to be cleared."""
        return any(state == HexLifecycleState.CORRUPTED for state in self.hex_states.values())

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

    def get_hex_state(self, hex_coords: Tuple[int, int]) -> Optional[HexLifecycleState]:
        """Get the current lifecycle state of a hex."""
        return self.hex_states.get(hex_coords, None)

    def set_hex_state(self, hex_coords: Tuple[int, int], state: HexLifecycleState) -> None:
        """Set the lifecycle state of a hex."""
        self.hex_states[hex_coords] = state
        save_progress()

    def is_hex_claimable(self, hex_coords: Tuple[int, int]) -> bool:
        """Check if a hex can be claimed."""
        state = self.get_hex_state(hex_coords)
        return state == HexLifecycleState.UNCLAIMED or state == HexLifecycleState.CORRUPTED

    def claim_hex(self, hex_coords: Tuple[int, int]) -> None:
        """Claim a hex."""
        current_state = self.get_hex_state(hex_coords)
        if current_state in [HexLifecycleState.CLAIMED, HexLifecycleState.RECLAIMED]:
            return
        assert current_state in [HexLifecycleState.UNCLAIMED, HexLifecycleState.CORRUPTED]
        
        # Only unfog neighbors if we're not in a corrupted state (normal progression)
        if current_state == HexLifecycleState.UNCLAIMED:
            for neighbor_coords in hex_neighbors(hex_coords):
                if self.get_hex_state(neighbor_coords) == HexLifecycleState.FOGGED:
                    self.set_hex_state(neighbor_coords, HexLifecycleState.UNCLAIMED)

        if current_state == HexLifecycleState.UNCLAIMED:
            # First claim - goes to CLAIMED state
            self.set_hex_state(hex_coords, HexLifecycleState.CLAIMED)
        elif current_state == HexLifecycleState.CORRUPTED:
            # Second claim (after corruption) - goes to RECLAIMED state
            self.set_hex_state(hex_coords, HexLifecycleState.RECLAIMED)
            
            # Check if this was the last corrupted hex - if so, restore fogged hexes
            if not self.has_uncompleted_corrupted_battles():
                self._restore_fogged_hexes_after_corruption()

    def _restore_fogged_hexes_after_corruption(self) -> None:
        """Restore fogged hexes that are adjacent to claimed/reclaimed hexes back to unclaimed state."""
        # Find all fogged hexes
        fogged_hexes = [coord for coord in self.hex_states if self.get_hex_state(coord) == HexLifecycleState.FOGGED]
        for hex_coords in fogged_hexes:
            # Check if this hex is adjacent to any claimed or reclaimed hex
            for neighbor_coords in hex_neighbors(hex_coords):
                neighbor_state = self.get_hex_state(neighbor_coords)
                if neighbor_state in [HexLifecycleState.CLAIMED, HexLifecycleState.RECLAIMED]:
                    self.set_hex_state(hex_coords, HexLifecycleState.UNCLAIMED)
                    break

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
    import upgrade_hexes
    global progress_manager
    progress_manager.solutions = {}
    progress_manager.unit_tiers = {}
    progress_manager.hex_states = {
        hex_coords: HexLifecycleState.FOGGED for hex_coords in upgrade_hexes.get_upgrade_hexes() + [battle.hex_coords for battle in battles.get_battles() if not battle.is_test]
    }
    progress_manager.hex_states[(0, 0)] = HexLifecycleState.UNCLAIMED
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
