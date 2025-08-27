import esper
from components.airborne import Airborne
from components.destination import Destination
from components.forced_movement import ForcedMovement
from components.orientation import FacingDirection, Orientation
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.velocity import Velocity
from components.status_effect import StatusEffects, WontPursue
from events import emit_event, DestinationTargetAcquiredEvent, DESTINATION_TARGET_ACQUIRED

class IdleProcessor(esper.Processor):
    def process(self, dt: float):
        for ent, (unit_state, velocity, destination, team, orientation) in esper.get_components(UnitState, Velocity, Destination, Team, Orientation):
            if esper.has_component(ent, Airborne) or esper.has_component(ent, ForcedMovement):
                continue
            if unit_state.state == State.IDLE:
                if esper.has_component(ent, StatusEffects) and any(isinstance(effect, WontPursue) for effect in esper.component_for_entity(ent, StatusEffects).active_effects()):
                    continue
                target = destination.target_strategy.target
                if target is not None:
                    emit_event(DESTINATION_TARGET_ACQUIRED, event=DestinationTargetAcquiredEvent(ent, target))
                velocity.x = 0
                velocity.y = 0
                if team.type == TeamType.TEAM1:
                    orientation.facing = FacingDirection.RIGHT
                else:
                    orientation.facing = FacingDirection.LEFT
