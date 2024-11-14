import esper
from components.destination import Destination
from components.orientation import FacingDirection, Orientation
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.velocity import Velocity
from events import emit_event, DestinationTargetAcquiredEvent, DESTINATION_TARGET_ACQUIRED

class IdleProcessor(esper.Processor):
    def process(self, dt: float):
        for ent, (unit_state, velocity, destination, team, orientation) in esper.get_components(UnitState, Velocity, Destination, Team, Orientation):
            if unit_state.state == State.IDLE:
                target = destination.target_strategy.target
                if target is not None:
                    emit_event(DESTINATION_TARGET_ACQUIRED, event=DestinationTargetAcquiredEvent(ent, target))
                velocity.x = 0
                velocity.y = 0
                if team.type == TeamType.TEAM1:
                    orientation.facing = FacingDirection.RIGHT
                else:
                    orientation.facing = FacingDirection.LEFT
