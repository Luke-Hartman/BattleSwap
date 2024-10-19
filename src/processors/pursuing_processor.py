"""Pursuing processor module for Battle Swap.

This module contains the PursuingProcessor class, which is responsible for
updating unit velocities for pursuit, checking target range, and updating orientation.
"""

import esper
import math
from components.position import Position
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.movement import Movement
from components.velocity import Velocity
from components.attack import MeleeAttack, ProjectileAttack
from components.orientation import Orientation, FacingDirection
from events import TargetInRangeEvent, TARGET_IN_RANGE, emit_event, TargetLostEvent, TARGET_LOST

class PursuingProcessor(esper.Processor):
    """Processor responsible for updating unit velocities for pursuit, checking target range, and updating orientation."""

    def process(self, dt: float):
        for ent, (unit_state, pos, movement, velocity, orientation) in esper.get_components(UnitState, Position, Movement, Velocity, Orientation):
            if unit_state.state == State.PURSUING and unit_state.target is not None:
                target_state = esper.component_for_entity(unit_state.target, UnitState)
                if target_state.state == State.DEAD:
                    emit_event(TARGET_LOST, event=TargetLostEvent(ent))
                else:
                    target_pos = esper.component_for_entity(unit_state.target, Position)
                    destination_pos = self.calculate_destination(ent, pos, target_pos)
                    target_dx = target_pos.x - pos.x
                    target_dy = target_pos.y - pos.y
                    destination_dx = destination_pos.x - pos.x
                    destination_dy = destination_pos.y - pos.y
                    target_distance = math.sqrt(target_dx**2 + target_dy**2)
                    destination_distance = math.sqrt(destination_dx**2 + destination_dy**2)
                    
                    orientation.facing = FacingDirection.RIGHT if destination_dx > 0 else FacingDirection.LEFT
                    
                    if self.is_target_in_range(ent, target_dx, target_dy, target_distance):
                        emit_event(TARGET_IN_RANGE, event=TargetInRangeEvent(ent, unit_state.target))
                        velocity.x = 0
                        velocity.y = 0
                    else:
                        velocity.x = (destination_dx / destination_distance) * movement.speed
                        velocity.y = (destination_dy / destination_distance) * movement.speed
            elif unit_state.state == State.IDLE:
                team = esper.component_for_entity(ent, Team)
                orientation.facing = FacingDirection.RIGHT if team.type == TeamType.TEAM1 else FacingDirection.LEFT
                velocity.x = 0
                velocity.y = 0
            else:
                velocity.x = 0
                velocity.y = 0

    def is_target_in_range(self, entity: int, dx: float, dy: float, distance: float) -> bool:
        melee_attack = esper.try_component(entity, MeleeAttack)
        if melee_attack:
            angle = math.atan2(abs(dy), abs(dx))
            return (
                melee_attack.range / 3 <= distance <= melee_attack.range and
                angle <= melee_attack.attack_angle / 2
            )
        
        projectile_attack = esper.try_component(entity, ProjectileAttack)
        if projectile_attack:
            return distance <= projectile_attack.range
        
        return False

    def calculate_destination(self, entity: int, pos: Position, target_pos: Position) -> Position:
        melee_attack = esper.try_component(entity, MeleeAttack)
        team = esper.component_for_entity(entity, Team)
        if melee_attack:
            offset = 2 * melee_attack.range / 3
            if team.type == TeamType.TEAM1:
                return Position(
                    x=target_pos.x - offset,
                    y=target_pos.y
                )
            else:
                return Position(
                    x=target_pos.x + offset,
                    y=target_pos.y
                )
        else:
            # For non-melee units, use the direct path
            return target_pos
