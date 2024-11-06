"""Targeting processor module for Battle Swap.

This module contains the TargetingProcessor class, which is responsible for
finding the nearest enemy for units without a target.
"""

import esper
from components.health import Health
from components.targetting_strategy import TargettingStrategyComponent, TargettingStrategyType
from components.unit_state import UnitState, State
from components.position import Position
from components.team import Team
from events import TargetAcquiredEvent, TARGET_ACQUIRED, emit_event

class TargetingProcessor(esper.Processor):
    """Processor responsible for finding targets for units."""

    def process(self, dt: float):
        for entity, (unit_state, position, team, targetting_strategy) in esper.get_components(UnitState, Position, Team, TargettingStrategyComponent):
            if unit_state.state == State.IDLE and unit_state.target is None:
                if targetting_strategy.type == TargettingStrategyType.NEAREST_ENEMY:
                    target = self.find_nearest_enemy(entity, position, team)
                elif targetting_strategy.type == TargettingStrategyType.STRONGEST_ALLY:
                    target = self.find_strongest_ally(entity, position, team)
                if target is not None:
                    unit_state.target = target
                    emit_event(TARGET_ACQUIRED, event=TargetAcquiredEvent(entity, target))

    def find_strongest_ally(self, entity: int, position: Position, team: Team) -> int:
        strongest_ally = None
        max_health = 0
        for ally, (ally_team, ally_state, health) in esper.get_components(Team, UnitState, Health):
            if ally_team.type == team.type and ally_state.state != State.DEAD:
                if health.current > max_health:
                    max_health = health.current
                    strongest_ally = ally
        return strongest_ally

    def find_nearest_enemy(self, entity: int, position: Position, team: Team) -> int:
        nearest_enemy = None
        min_distance = float('inf')
        for enemy, (enemy_pos, enemy_team, enemy_state) in esper.get_components(Position, Team, UnitState):
            if enemy_team.type != team.type and enemy_state.state != State.DEAD:
                x_weight = 1
                y_weight = 2
                # Higher weight makes units less likely to target in that dimension.
                distance = ((x_weight * (position.x - enemy_pos.x)) ** 2 + (y_weight * (position.y - enemy_pos.y)) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
        return nearest_enemy
