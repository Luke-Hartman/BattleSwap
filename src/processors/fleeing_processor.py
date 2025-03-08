"""Fleeing processor module for Battle Swap.

Fleeing units run away from a specific entity, and they ignore their destination/target/ability conditions.
"""

import esper
from components.movement import Movement
from game_constants import gc
from components.orientation import FacingDirection, Orientation
from components.position import Position
from components.status_effect import Fleeing, StatusEffects
from components.unit_state import State, UnitState
from components.velocity import Velocity
from events import FLEEING_EXPIRED, FLEEING_STARTED, FleeingExpiredEvent, FleeingStartedEvent, emit_event

class FleeingProcessor(esper.Processor):
    """Processor responsible for fleeing units."""

    def process(self, dt: float):
        for ent, (unit_state, pos, velocity, movement, orientation, status_effects) in esper.get_components(UnitState, Position, Velocity, Movement, Orientation, StatusEffects):
            if unit_state.state == State.DEAD:
                continue
            if unit_state.state != State.FLEEING:
                for effect in status_effects.active_effects():
                    if isinstance(effect, Fleeing):
                        emit_event(FLEEING_STARTED, event=FleeingStartedEvent(ent))
            if unit_state.state == State.FLEEING:
                fleeing_effect = None
                for effect in status_effects.active_effects():
                    if isinstance(effect, Fleeing):
                        fleeing_effect = effect
                        break
                if fleeing_effect is None:
                    emit_event(FLEEING_EXPIRED, event=FleeingExpiredEvent(ent))
                    break
                afraid_of = fleeing_effect.entity
                afraid_of_pos = esper.component_for_entity(afraid_of, Position)
                dx = pos.x - afraid_of_pos.x
                dy = pos.y - afraid_of_pos.y
                distance = pos.distance(afraid_of_pos, y_bias=None)
                if distance == 0:
                    dx = 1
                    dy = 0
                    distance = 1
                fleeing_speed = min(gc.FLEEING_SPEED, movement.speed)
                velocity.x = dx / distance * fleeing_speed
                velocity.y = dy / distance * fleeing_speed
                orientation.facing = FacingDirection.LEFT if dx < 0 else FacingDirection.RIGHT
