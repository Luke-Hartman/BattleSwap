"""Pursuing processor module for Battle Swap.

This module contains the PursuingProcessor class, which is responsible for
updating unit velocities for pursuit and checking if targets are in range.
"""

import esper
from components.position import Position
from components.unit_state import UnitState, State
from components.movement import Movement
from components.velocity import Velocity
from components.attack import MeleeAttack, ProjectileAttack
from events import TargetInRangeEvent, TARGET_IN_RANGE, emit_event, TargetLostEvent, TARGET_LOST

class PursuingProcessor(esper.Processor):
    """Processor responsible for updating unit velocities for pursuit and checking target range."""

    def process(self, dt: float):
        for ent, (unit_state, pos, movement, velocity) in esper.get_components(UnitState, Position, Movement, Velocity):
            if unit_state.state == State.PURSUING and unit_state.target is not None:
                target_state = esper.component_for_entity(unit_state.target, UnitState)
                if target_state.state == State.DEAD:
                    emit_event(TARGET_LOST, event=TargetLostEvent(ent))
                else:
                    target_pos = esper.component_for_entity(unit_state.target, Position)
                    dx = target_pos.x - pos.x
                    dy = target_pos.y - pos.y
                    distance = (dx**2 + dy**2)**0.5
                    
                    attack_range = self.get_attack_range(ent)
                    if attack_range is not None and distance <= attack_range:
                        emit_event(TARGET_IN_RANGE, event=TargetInRangeEvent(ent, unit_state.target))
                    else:
                        velocity.x = (dx / distance) * movement.speed
                        velocity.y = (dy / distance) * movement.speed
            else:
                velocity.x = 0
                velocity.y = 0

    def get_attack_range(self, entity: int) -> float | None:
        melee_attack = esper.try_component(entity, MeleeAttack)
        if melee_attack:
            return melee_attack.range
        
        projectile_attack = esper.try_component(entity, ProjectileAttack)
        if projectile_attack:
            return projectile_attack.range
        
        return None
