"""Progress manager for the game."""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import battles
from components.unit_type import UnitType
from hex_grid import hex_neighbors


class Solution:
    def __init__(self, hex_coords: Tuple[int, int], unit_placements: List[Tuple[UnitType, Tuple[int, int]]]):
        self.hex_coords = hex_coords
        self.unit_placements = unit_placements

class ProgressManager:

    def __init__(self):
        self.solutions: Dict[Tuple[int, int], Solution] = {}

    def available_units(self, current_battle: Optional[battles.Battle]) -> Dict[UnitType, int]:
        """Get the available units for the player."""
        units = defaultdict(int)
        units.update(battles.starting_units)
        for coords in self.solutions:
            if current_battle is None or current_battle.hex_coords != coords:
                battle = battles.get_battle_coords(coords)
            else:
                battle = current_battle
            for (unit_type, _) in battle.enemies:
                units[unit_type] += 1
            for (unit_type, _) in self.solutions[coords].unit_placements:
                units[unit_type] -= 1
        if current_battle is not None and current_battle.hex_coords not in self.solutions and current_battle.allies is not None:
            for (unit_type, _) in current_battle.allies:
                units[unit_type] -= 1
        for unit_type, count in units.items():
            assert count >= 0
        return units

    def available_battles(self) -> List[Tuple[int, int]]:
        """Get the available battles for the player."""
        available_battles = [(0, 0)] # 0, 0 is always available
        progress = True
        while progress:
            progress = False
            for battle in battles.get_battles():
                coords = battle.hex_coords
                if (
                    coords not in available_battles
                    and not battle.is_test
                    and any(
                        neighbor in self.solutions for neighbor in hex_neighbors(coords))
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
