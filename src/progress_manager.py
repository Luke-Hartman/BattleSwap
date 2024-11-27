"""Progress manager for the game."""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import battles
from components.unit_type import UnitType


class Solution:
    def __init__(self, battle_id: str, unit_placements: List[Tuple[UnitType, Tuple[int, int]]]):
        self.battle_id = battle_id
        self.unit_placements = unit_placements

class ProgressManager:

    def __init__(self):
        self.solutions: Dict[str, Solution] = {}

    def available_units(self, current_battle_id: Optional[str]) -> Dict[UnitType, int]:
        """Get the available units for the player."""
        units = defaultdict(int)
        units.update(battles.starting_units)
        for battle in battles.get_battles():
            if battle.id in self.solutions:
                for (unit_type, _) in battle.enemies:
                    units[unit_type] += 1
                if current_battle_id != battle.id:
                    for (unit_type, _) in self.solutions[battle.id].unit_placements:
                        units[unit_type] -= 1
        for unit_type, count in units.items():
            assert count >= 0
        return units

    def available_battles(self) -> List[str]:
        """Get the available battles for the player."""
        available_battles = []
        progress = True
        while progress:
            progress = False
            for battle in battles.get_battles():
                if (
                    battle.id not in available_battles
                    and not battle.is_test
                    and all(dep in self.solutions for dep in battle.dependencies)
                ):
                    available_battles.append(battle.id)
                    progress = True
        return available_battles

    def save_solution(self, solution: Solution) -> None:
        """Save a solution."""
        self.solutions[solution.battle_id] = solution

