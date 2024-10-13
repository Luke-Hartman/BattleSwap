"""Targeting processor module for Battle Swap.

This module contains the TargetingProcessor class, which is responsible for
finding the nearest enemy for units without a target.
"""

import esper
from components.unit_state import UnitState, State
from components.position import Position
from components.team import Team
from events import TargetAcquiredEvent, TARGET_ACQUIRED, emit_event

class TargetingProcessor(esper.Processor):
    """Processor responsible for finding targets for units."""

    def process(self, dt: float):
        for entity, (unit_state, position, team) in esper.get_components(UnitState, Position, Team):
            if unit_state.state == State.IDLE and unit_state.target is None:
                target = self.find_nearest_enemy(entity, position, team)
                if target is not None:
                    unit_state.target = target
                    emit_event(TARGET_ACQUIRED, event=TargetAcquiredEvent(entity, target))

    def find_nearest_enemy(self, entity: int, position: Position, team: Team) -> int:
        nearest_enemy = None
        min_distance = float('inf')
        for enemy, (enemy_pos, enemy_team) in esper.get_components(Position, Team):
            if enemy_team.type != team.type:
                distance = ((position.x - enemy_pos.x) ** 2 + (position.y - enemy_pos.y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
        return nearest_enemy
