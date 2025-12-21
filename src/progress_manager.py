"""Progress manager for the game."""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
from enum import Enum

from pydantic import BaseModel, ValidationError, field_serializer, field_validator
from platformdirs import user_config_dir

from events import PLAY_SOUND, PlaySoundEvent, emit_event
import battles
from components.unit_type import UnitType
from components.unit_tier import UnitTier
from components.item import ItemType
from components.spell_type import SpellType
from point_values import unit_values, item_values, spell_values
from hex_grid import hex_neighbors
from game_constants import gc
import random

# Current version of the progress manager
# Increment this when making breaking changes to save file format
CURRENT_VERSION = 4

# Starting hex coordinates that are initially available
STARTING_HEXES = [(0, 0), (1, -1), (0, 1)]


class Package(BaseModel):
    """Represents a package of items or spells with a total value of 300 points."""
    items: Dict[ItemType, int] = {}
    spells: Dict[SpellType, int] = {}
    total_value: int = 300
    
    
    def model_post_init(self, __context) -> None:
        """Validate the complete package after initialization."""
        if self.items and self.spells:
            raise ValueError("Package cannot contain both items and spells")
        if not self.items and not self.spells:
            raise ValueError("Package must contain either items or spells")
        
        # Calculate total value
        total = 0
        for item_type, count in self.items.items():
            total += item_values[item_type] * count
        for spell_type, count in self.spells.items():
            total += spell_values[spell_type] * count
            
        if total != 300:
            raise ValueError(f"Package must have exactly 300 points, got {total}")
    
    @field_serializer('items')
    def serialize_items(self, items: Dict[ItemType, int]) -> Dict[str, int]:
        return {item_type.value: count for item_type, count in items.items()}
    
    @field_serializer('spells')
    def serialize_spells(self, spells: Dict[SpellType, int]) -> Dict[str, int]:
        return {spell_type.value: count for spell_type, count in spells.items()}
    
    @field_validator('items', mode='before')
    def parse_items(cls, value: Any) -> Dict[ItemType, int]:
        if isinstance(value, dict):
            if all(isinstance(k, str) for k in value.keys()):
                return {ItemType(item_type): count for item_type, count in value.items()}
            return value
        return value
    
    @field_validator('spells', mode='before')
    def parse_spells(cls, value: Any) -> Dict[SpellType, int]:
        if isinstance(value, dict):
            if all(isinstance(k, str) for k in value.keys()):
                return {SpellType(spell_type): count for spell_type, count in value.items()}
            return value
        return value

class HexLifecycleState(Enum):
    """Enum representing the lifecycle state of a hex (battle or upgrade)."""
    FOGGED = "fogged"        # Not adjacent to any claimed hex, inaccessible
    UNCLAIMED = "unclaimed"  # Adjacent to claimed hex, accessible but never claimed/solved
    CLAIMED = "claimed"      # Claimed/solved once, never corrupted
    CORRUPTED = "corrupted"  # Claimed/solved once, then corrupted (can be claimed/solved again)
    RECLAIMED = "reclaimed"  # Claimed/solved twice (once normal, once corrupted)

def calculate_points_for_units(units: List[Tuple[UnitType, Tuple[float, float], List[ItemType]]]) -> int:
    """Calculate total points for a list of unit placements."""
    total_points = 0
    for unit_type, _, items in units:
        total_points += unit_values[unit_type]
        total_points += sum(item_values[item_type] for item_type in items)
    return total_points


def calculate_total_available_points() -> int:
    """Calculate total points available from starting units, items, spells and completed battles."""
    points = sum(unit_values[unit_type] * count for unit_type, count in battles.starting_units.items())
    points += sum(item_values[item_type] * count for item_type, count in progress_manager.acquired_items.items())
    points += sum(spell_values[spell_type] * count for spell_type, count in progress_manager.acquired_spells.items())
    for battle in battles.get_battles():
        if battle.hex_coords in progress_manager.solutions:
            solution = progress_manager.solutions[battle.hex_coords]
            points += sum(unit_values[unit_type] + sum(item_values[item_type] for item_type in items) for unit_type, _, items in battle.enemies)
            points -= sum(unit_values[unit_type] + sum(item_values[item_type] for item_type in items) for unit_type, _, items in solution.unit_placements)
            points -= sum(spell_values[spell_type] for spell_type, _, _ in solution.spell_placements)
    return points


class Solution(BaseModel):
    hex_coords: Tuple[int, int]
    unit_placements: List[Tuple[UnitType, Tuple[float, float], List[ItemType]]]
    spell_placements: List[Tuple[SpellType, Tuple[float, float], int]]
    solved_corrupted: bool

    @field_serializer('hex_coords')
    def serialize_hex_coords(self, hex_coords: Tuple[int, int]) -> List[int]:
        return list(hex_coords)
    
    @field_serializer('unit_placements')
    def serialize_unit_placements(self, unit_placements: List[Tuple[UnitType, Tuple[float, float], List[ItemType]]]) -> List[List]:
        """Serialize unit placements for JSON storage."""
        result = []
        for unit_type, position, items in unit_placements:
            result.append([unit_type.value, list(position), [item.value for item in items]])
        return result
    
    @field_serializer('spell_placements')
    def serialize_spell_placements(self, spell_placements: List[Tuple[SpellType, Tuple[float, float], int]]) -> List[List]:
        """Serialize spell placements for JSON storage."""
        result = []
        for spell_type, position, team in spell_placements:
            result.append([spell_type.value, list(position), team])
        return result

    @field_validator('hex_coords', mode='before')
    def parse_hex_coords(cls, value: Any) -> Tuple[int, int]:
        if isinstance(value, list):
            return tuple(value)
        return value
    
    @field_validator('unit_placements', mode='before')
    def parse_unit_placements(cls, value: Any) -> List[Tuple[UnitType, Tuple[float, float], List[ItemType]]]:
        """Parse unit placements from JSON storage."""
        result = []
        for item in value:
            unit_type_str, position_list, items_list = item
            unit_type = UnitType(unit_type_str)
            position = tuple(position_list)
            items = [ItemType(item_str) for item_str in items_list]
            result.append((unit_type, position, items))
        return result
    
    @field_validator('spell_placements', mode='before')
    def parse_spell_placements(cls, value: Any) -> List[Tuple[SpellType, Tuple[float, float], int]]:
        """Parse spell placements from JSON storage."""
        if value is None:
            return []
        result = []
        for item in value:
            spell_type_str, position_list, team = item
            spell_type = SpellType(spell_type_str)
            position = tuple(position_list)
            result.append((spell_type, position, team))
        return result




class ProgressManager(BaseModel):
    version: int = CURRENT_VERSION
    solutions: Dict[Tuple[int, int], Solution] = {}
    game_completed: bool = False
    game_completed_corruption: bool = False
    pending_packages: Optional[List[Package]] = None
    unit_tiers: Dict[UnitType, UnitTier] = {}
    hex_states: Dict[Tuple[int, int], HexLifecycleState] = {}
    upgrade_tutorial_shown: bool = False
    acquired_items: Dict[ItemType, int] = {}
    acquired_spells: Dict[SpellType, int] = {}
    packages_given: int = 0

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
    
    @field_serializer('acquired_items')
    def serialize_acquired_items(self, acquired_items: Dict[ItemType, int]) -> Dict[str, int]:
        return {item_type.value: count for item_type, count in acquired_items.items()}
    
    @field_serializer('acquired_spells')
    def serialize_acquired_spells(self, acquired_spells: Dict[SpellType, int]) -> Dict[str, int]:
        return {spell_type.value: count for spell_type, count in acquired_spells.items()}
    
    @field_serializer('pending_packages')
    def serialize_pending_packages(self, pending_packages: Optional[List[Package]]) -> Optional[List[Dict[str, Any]]]:
        return [package.model_dump() for package in pending_packages] if pending_packages is not None else None
    
    @field_validator('pending_packages', mode='before')
    def parse_pending_packages(cls, value: Any) -> Optional[List[Package]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [Package.model_validate(package_data) for package_data in value]
        return value

    @field_validator('hex_states', mode='before')
    def parse_hex_states(cls, value: Any) -> Dict[Tuple[int, int], HexLifecycleState]:
        if isinstance(value, dict):
            result = {}
            for key, state_value in value.items():
                coords = tuple(json.loads(key))
                result[coords] = HexLifecycleState(state_value)
            return result
        return value
    
    @field_validator('acquired_items', mode='before')
    def parse_acquired_items(cls, value: Any) -> Dict[ItemType, int]:
        if isinstance(value, dict):
            return {ItemType(item_type_str): count for item_type_str, count in value.items()}
        return value
    
    @field_validator('acquired_spells', mode='before')
    def parse_acquired_spells(cls, value: Any) -> Dict[SpellType, int]:
        if isinstance(value, dict):
            return {SpellType(spell_type_str): count for spell_type_str, count in value.items()}
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
            for (unit_type, _, _) in battle.enemies:
                units[unit_type] += 1
            for (unit_type, _, _) in self.solutions[coords].unit_placements:
                units[unit_type] -= 1
        # Handle units from the current battle
        if current_battle is not None and current_battle.allies is not None:
            if current_battle.hex_coords in self.solutions:
                for unit_type, _, _ in current_battle.enemies:
                    units[unit_type] += 1
            for (unit_type, _, _) in current_battle.allies:
                units[unit_type] -= 1
        for unit_type, count in units.items():
            assert count >= 0, str(units)
        return units

    def available_items(self, current_battle: Optional[battles.Battle]) -> Dict[ItemType, int]:
        """Get the available items for the player."""
        items = defaultdict(int)
        items.update(self.acquired_items)
        # Handle items from battles other than the current one
        for coords in self.solutions:
            if current_battle is not None and current_battle.hex_coords == coords:
                continue
            battle = battles.get_battle_coords(coords)
            # Subtract items used in completed battles
            for (unit_type, _, unit_items) in self.solutions[coords].unit_placements:
                for item_type in unit_items:
                    items[item_type] -= 1
        # Handle items from the current battle
        if current_battle is not None and current_battle.allies is not None:
            for (unit_type, _, unit_items) in current_battle.allies:
                for item_type in unit_items:
                    items[item_type] -= 1
        for item_type, count in items.items():
            assert count >= 0, str(items)
        return items

    def available_spells(self, current_battle: Optional[battles.Battle]) -> Dict[SpellType, int]:
        """Get the available spells for the player."""
        spells = defaultdict(int)
        spells.update(self.acquired_spells)
        # Handle spells from battles other than the current one
        for coords in self.solutions:
            if current_battle is not None and current_battle.hex_coords == coords:
                continue
            for (spell_type, _, _) in self.solutions[coords].spell_placements:
                spells[spell_type] -= 1
        # Handle spells from the current battle
        if current_battle is not None and hasattr(current_battle, 'spells') and current_battle.spells is not None:
            for (spell_type, _, _) in current_battle.spells:
                spells[spell_type] -= 1
        for spell_type, count in spells.items():
            assert count >= 0, str(spells)
        return spells

    def get_battles_including_solutions(self) -> List[battles.Battle]:
        """Get all battles, and include ally positions for solved battles."""
        all_battles = battles.get_battles()
        for battle in all_battles:
            if battle.hex_coords in self.solutions:
                battle.allies = self.solutions[battle.hex_coords].unit_placements
                battle.spells = self.solutions[battle.hex_coords].spell_placements
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
    
    def count_reclaimed_corrupted_battles(self) -> int:
        """Count the number of reclaimed corrupted battle hexes (not upgrade hexes).
        
        Returns:
            The number of battle hexes that have been reclaimed (solved corrupted).
        """
        from upgrade_hexes import is_upgrade_hex
        reclaimed_count = 0
        for coords, state in self.hex_states.items():
            if state == HexLifecycleState.RECLAIMED:
                # Only count battle hexes, not upgrade hexes
                if not is_upgrade_hex(coords):
                    reclaimed_count += 1
        return reclaimed_count
    
    def should_show_package_selection(self) -> bool:
        """Check if package selection should be shown based on reclaimed corrupted battles.
        
        Returns:
            True if the player has reclaimed corrupted battles but hasn't received enough packages.
        """
        reclaimed_battles = self.count_reclaimed_corrupted_battles()
        # Player should get 1 package per reclaimed corrupted battle
        expected_packages = reclaimed_battles // gc.CORRUPTION_BATTLE_COUNT
        # If player is short on packages, show the selection panel
        if expected_packages > self.packages_given:
            # Generate packages if we don't have pending ones
            if self.pending_packages is None:
                self.pending_packages = self._generate_packages()
                save_progress()
            return True
        return False

    def mark_congratulations_shown(self) -> None:
        self.game_completed = True
        save_progress()

    def mark_corruption_congratulations_shown(self) -> None:
        self.game_completed_corruption = True
        save_progress()
    
    def mark_package_selection_completed(self) -> None:
        """Mark that package selection has been completed."""
        self.pending_packages = None  # Clear the packages
        self.packages_given += 1  # Increment the count of packages given
        save_progress()
    
    def _generate_packages(self) -> List[Package]:
        """Generate 3 random packages avoiding duplicates.
        
        Returns:
            List of 3 unique packages with 300 points each.
        """
        # Create lists of all available items and spells
        all_items = list(ItemType)
        all_spells = list(SpellType)
        
        # Shuffle to randomize selection
        random.shuffle(all_items)
        random.shuffle(all_spells)
        
        packages = []
        used_items = set()
        used_spells = set()
        
        # Generate 3 packages, alternating between items and spells
        for i in range(3):
            # Alternate between items and spells
            if i % 2 == 0:
                # Try items first
                available_items = [item for item in all_items if item not in used_items]
                if available_items:
                    item_type = available_items[0]
                    quantity = 300 // item_values[item_type]
                    packages.append(Package(items={item_type: quantity}, spells={}))
                    used_items.add(item_type)
                else:
                    # Fallback to spells
                    available_spells = [spell for spell in all_spells if spell not in used_spells]
                    if available_spells:
                        spell_type = available_spells[0]
                        quantity = 300 // spell_values[spell_type]
                        packages.append(Package(items={}, spells={spell_type: quantity}))
                        used_spells.add(spell_type)
            else:
                # Try spells first
                available_spells = [spell for spell in all_spells if spell not in used_spells]
                if available_spells:
                    spell_type = available_spells[0]
                    quantity = 300 // spell_values[spell_type]
                    packages.append(Package(items={}, spells={spell_type: quantity}))
                    used_spells.add(spell_type)
                else:
                    # Fallback to items
                    available_items = [item for item in all_items if item not in used_items]
                    if available_items:
                        item_type = available_items[0]
                        quantity = 300 // item_values[item_type]
                        packages.append(Package(items={item_type: quantity}, spells={}))
                        used_items.add(item_type)
        
        return packages
    
    def select_package(self, package: Package) -> None:
        """Handle package selection by adding items/spells and marking selection complete.
        
        Args:
            package: The selected package containing items or spells.
        """
        # Add items or spells from the package to the acquired inventory
        if package.items:
            self.add_package_items(package.items)
        if package.spells:
            self.add_package_spells(package.spells)
        
        # Mark package selection as completed
        self.mark_package_selection_completed()
    
    def add_package_items(self, items: Dict[ItemType, int]) -> None:
        """Add items from a selected package to the acquired items.
        
        Args:
            items: Dictionary mapping item types to quantities to add.
        """
        for item_type, count in items.items():
            self.acquired_items[item_type] = self.acquired_items.get(item_type, 0) + count
        save_progress()
    
    def add_package_spells(self, spells: Dict[SpellType, int]) -> None:
        """Add spells from a selected package to the acquired spells.
        
        Args:
            spells: Dictionary mapping spell types to quantities to add.
        """
        for spell_type, count in spells.items():
            self.acquired_spells[spell_type] = self.acquired_spells.get(spell_type, 0) + count
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
        """Corrupt a number of completed battles and claimed upgrade hexes with random selection."""
        hexes_to_corrupt = []
        
        for _ in range(gc.CORRUPTION_BATTLE_COUNT):
            # Get valid corruption targets (starting hex or adjacent to corrupted hexes)
            corrupted_hexes = [
                coords for coords, state in self.hex_states.items() 
                if state in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]
            ]
            valid_targets = []
            
            # Always include starting hexes if they're claimed
            for starting_hex in STARTING_HEXES:
                if (starting_hex in self.hex_states and 
                    self.hex_states[starting_hex] == HexLifecycleState.CLAIMED):
                    valid_targets.append(starting_hex)
            
            # Add all claimed hexes that are adjacent to any corrupted hex
            for coords, state in self.hex_states.items():
                if state == HexLifecycleState.CLAIMED:
                    # Check if this hex is adjacent to any corrupted hex
                    neighbors = hex_neighbors(coords)
                    if any(neighbor in corrupted_hexes for neighbor in neighbors):
                        valid_targets.append(coords)
            
            if not valid_targets:
                raise ValueError("No valid targets found for corruption")
            
            # Randomly select one hex to corrupt
            hex_to_corrupt = random.choice(valid_targets)
            hexes_to_corrupt.append(hex_to_corrupt)
            
            # Immediately corrupt this hex so it can be used for adjacency in next iteration
            self.set_hex_state(hex_to_corrupt, HexLifecycleState.CORRUPTED)
        
        # Fog all unclaimed battle hexes to prevent new battle claims during corruption
        # (but allow upgrade hexes to still be claimed)
        from upgrade_hexes import is_upgrade_hex
        unclaimed_hexes = [coord for coord in self.hex_states if self.hex_states[coord] == HexLifecycleState.UNCLAIMED]
        for coords in unclaimed_hexes:
            # Only fog battle hexes, not upgrade hexes
            if not is_upgrade_hex(coords):
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

    def clear_hex_state(self, hex_coords: Tuple[int, int]) -> None:
        """Clear the lifecycle state of a hex."""
        if hex_coords in self.hex_states:
            del self.hex_states[hex_coords]
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

        from upgrade_hexes import is_upgrade_hex
        if current_state == HexLifecycleState.UNCLAIMED:
            # First claim - goes to CLAIMED state
            self.set_hex_state(hex_coords, HexLifecycleState.CLAIMED)
            if is_upgrade_hex(hex_coords):
                emit_event(PLAY_SOUND, event=PlaySoundEvent(filename="claim_upgrade.wav", volume=0.5))
        elif current_state == HexLifecycleState.CORRUPTED:
            # Second claim (after corruption) - goes to RECLAIMED state
            self.set_hex_state(hex_coords, HexLifecycleState.RECLAIMED)
            if is_upgrade_hex(hex_coords):
                emit_event(PLAY_SOUND, event=PlaySoundEvent(filename="reclaim_upgrade.wav", volume=0.5))
            
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

    def should_show_upgrade_tutorial(self) -> bool:
        """Check if the upgrade tutorial should be shown."""
        return not self.upgrade_tutorial_shown and self._has_claimed_upgrade_hexes()

    def mark_upgrade_tutorial_shown(self) -> None:
        """Mark the upgrade tutorial as shown."""
        self.upgrade_tutorial_shown = True
        save_progress()

    def _has_claimed_upgrade_hexes(self) -> bool:
        """Check if any upgrade hexes have been claimed."""
        import upgrade_hexes
        for coords, state in self.hex_states.items():
            if upgrade_hexes.is_upgrade_hex(coords) and state in [HexLifecycleState.CLAIMED, HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]:
                return True
        return False

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
    for starting_hex in STARTING_HEXES:
        progress_manager.hex_states[starting_hex] = HexLifecycleState.UNCLAIMED
    progress_manager.upgrade_tutorial_shown = False
    progress_manager.pending_packages = None
    progress_manager.acquired_items.clear()
    progress_manager.acquired_spells.clear()
    progress_manager.packages_given = 0
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
