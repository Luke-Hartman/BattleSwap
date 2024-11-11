"""Pursuing processor module for Battle Swap.

This module contains the PursuingProcessor class, which is responsible for
updating unit velocities for pursuit, checking target range, and updating orientation.
"""

import esper
import math
from components.destination import Destination
from components.position import Position
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.movement import Movement
from components.velocity import Velocity
from components.orientation import Orientation, FacingDirection
from events import emit_event, DestinationTargetAcquiredEvent, DESTINATION_TARGET_ACQUIRED, DestinationTargetLostEvent, DESTINATION_TARGET_LOST

class PursuingProcessor(esper.Processor):
    """Processor responsible for moving units towards their destination."""

    def process(self, dt: float):
        for ent, (unit_state, pos, movement, velocity, orientation, destination) in esper.get_components(UnitState, Position, Movement, Velocity, Orientation, Destination):
            target = destination.target_strategy.target
            # Note that the target is set by the targetting processor, but we check here whether to change state/etc
            if unit_state.state == State.IDLE:
                if target is not None:
                    emit_event(DESTINATION_TARGET_ACQUIRED, event=DestinationTargetAcquiredEvent(ent, target))
            elif unit_state.state == State.PURSUING and target is None:
                emit_event(DESTINATION_TARGET_LOST, event=DestinationTargetLostEvent(ent))
            if unit_state.state == State.PURSUING and target is not None:
                target_pos = esper.component_for_entity(target, Position)
                team = esper.component_for_entity(ent, Team)
                orientation.facing = FacingDirection.RIGHT if target_pos.x > pos.x else FacingDirection.LEFT
                destination_x = target_pos.x - destination.x_offset * orientation.facing.value

                destination_dx = destination_x - pos.x
                destination_dy = target_pos.y - pos.y
                destination_distance = math.sqrt(destination_dx**2 + destination_dy**2)

                if destination_distance < 1:
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
