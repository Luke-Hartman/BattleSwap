"""Pursuing processor module for Battle Swap.

This module contains the PursuingProcessor class, which is responsible for
updating unit velocities for pursuit, checking target range, and updating orientation.
"""

import esper
import math
from components.airborne import Airborne
from components.corruption import IncreasedMovementSpeedComponent
from components.destination import Destination
from components.forced_movement import ForcedMovement
from components.position import Position
from components.status_effect import InfantryBannerBearerMovementSpeedBuff, StatusEffects
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.movement import Movement
from components.velocity import Velocity
from components.orientation import Orientation, FacingDirection
from events import emit_event, DestinationTargetLostEvent, DESTINATION_TARGET_LOST, DESTINATION_REACHED, DestinationReachedEvent

class PursuingProcessor(esper.Processor):
    """Processor responsible for moving units towards their destination."""

    def process(self, dt: float):
        for ent, (unit_state, pos, movement, velocity, orientation, destination) in esper.get_components(UnitState, Position, Movement, Velocity, Orientation, Destination):
            if esper.has_component(ent, Airborne) or esper.has_component(ent, ForcedMovement):
                continue
            target = destination.target_strategy.target
            if unit_state.state == State.PURSUING and target is None:
                emit_event(DESTINATION_TARGET_LOST, event=DestinationTargetLostEvent(ent))
            if unit_state.state == State.PURSUING and target is not None:
                target_pos = esper.component_for_entity(target, Position)
                orientation.facing = FacingDirection.RIGHT if target_pos.x > pos.x else FacingDirection.LEFT
                destination_pos = destination.get_destination_position(ent, dt)
                destination_dx = destination_pos.x - pos.x
                destination_dy = destination_pos.y - pos.y
                destination_distance = math.sqrt(destination_dx**2 + destination_dy**2)

                if destination_distance < destination.min_distance:
                    velocity.x = 0
                    velocity.y = 0
                    emit_event(DESTINATION_REACHED, event=DestinationReachedEvent(ent))
                else:
                    if dt == 0:
                        speed = 0
                    else:
                        status_effects = esper.try_component(ent, StatusEffects)
                        speed = movement.speed
                        for effect in status_effects.active_effects():
                            if isinstance(effect, InfantryBannerBearerMovementSpeedBuff):
                                speed = effect.movement_speed
                        movement_speed_component = esper.try_component(ent, IncreasedMovementSpeedComponent)
                        if movement_speed_component is not None:
                            speed *= 1 + movement_speed_component.increase_percent / 100
                        speed = min(
                            destination_distance/dt, # 30 ticks per second
                            speed
                        )
                    velocity.x = (destination_dx / destination_distance) * speed
                    velocity.y = (destination_dy / destination_distance) * speed
