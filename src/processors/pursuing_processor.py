"""Pursuing processor module for Battle Swap.

This module contains the PursuingProcessor class, which is responsible for
updating unit velocities for pursuit and checking if targets are in range.
"""

import esper
from components.position import Position
from components.unit_state import UnitState, State
from components.movement import Movement
from components.velocity import Velocity
from components.attack import Attack
from events import TargetInRangeEvent, TARGET_IN_RANGE, emit_event

class PursuingProcessor(esper.Processor):
    """Processor responsible for updating unit velocities for pursuit and checking target range."""

    def process(self, dt: float):
        for ent, (unit_state, pos, movement, velocity, attack) in esper.get_components(UnitState, Position, Movement, Velocity, Attack):
            if unit_state.state == State.PURSUING and unit_state.target is not None:
                target_pos = esper.component_for_entity(unit_state.target, Position)
                dx = target_pos.x - pos.x
                dy = target_pos.y - pos.y
                distance = (dx**2 + dy**2)**0.5
                if distance > 0:
                    velocity.x = (dx / distance) * movement.speed
                    velocity.y = (dy / distance) * movement.speed
                
                if self.is_target_in_range(ent, unit_state.target, attack.range):
                    emit_event(TARGET_IN_RANGE, event=TargetInRangeEvent(ent, unit_state.target))
            else:
                velocity.x = 0
                velocity.y = 0

    def is_target_in_range(self, entity: int, target: int, attack_range: float) -> bool:
        entity_pos = esper.component_for_entity(entity, Position)
        target_pos = esper.component_for_entity(target, Position)
        distance = ((entity_pos.x - target_pos.x) ** 2 + (entity_pos.y - target_pos.y) ** 2) ** 0.5
        return distance <= attack_range
