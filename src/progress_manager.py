"""Progress manager for the game."""

from collections import defaultdict
from typing import Dict, List, Tuple

import battles
from components.unit_type import UnitType


class Solution:
    def __init__(self, battle_id: str, unit_placements: List[Tuple[UnitType, Tuple[int, int]]]):
        self.battle_id = battle_id
        self.unit_placements = unit_placements

class ProgressManager:

    def __init__(self):
        self.solutions: Dict[str, Solution] = {}

    def available_units(self) -> Dict[UnitType, int]:
        """Get the available units for the player."""
        units = defaultdict(int)
        units.update(battles.starting_units)
        for battle_id, unit_placements in battles.enemies.items():
            if battle_id in self.solutions:
                for (unit_type, _) in unit_placements:
                    units[unit_type] += 1
                for (unit_type, _) in self.solutions[battle_id].unit_placements:
                    units[unit_type] -= 1
        print(units)
        for unit_type, count in units.items():
            assert count >= 0
        return units

    def available_battles(self) -> List[str]:
        """Get the available battles for the player."""
        available_battles = []
        progress = True
        while progress:
            progress = False
            for battle_id, dependencies in battles.dependencies.items():
                if battle_id not in available_battles and all(dep in self.solutions for dep in dependencies):
                    available_battles.append(battle_id)
                    progress = True
        return available_battles

    def save_solution(self, solution: Solution) -> None:
        """Save a solution."""
        self.solutions[solution.battle_id] = solution

