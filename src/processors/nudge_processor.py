"""Processor that slightly repels living units from each other."""

import esper

from components.no_nudge import NoNudge
from components.position import Position
from components.unit_state import UnitState, State
from game_constants import gc

class NudgeProcessor:

    def process(self, dt: float):
        pass
        # DISABLED FOR NOW
        # for entity, (pos, unit_state) in esper.get_components(Position, UnitState):
        #     if unit_state.state != State.PURSUING or esper.has_component(entity, NoNudge):
        #         continue
        #     for other_entity, (other_pos, other_unit_state) in esper.get_components(Position, UnitState):
        #         if other_entity == entity or other_unit_state.state == State.DEAD or esper.has_component(other_entity, NoNudge):
        #             continue
        #         distance = pos.distance(other_pos, 1)
        #         if distance < gc.NUDGE_DISTANCE:
        #             if distance < 0.001:
        #                 continue
        #             nudge_distance = min(gc.NUDGE_DISTANCE - distance, 1)
        #             pos.x += nudge_distance * (pos.x - other_pos.x) / distance
        #             pos.y += nudge_distance * (pos.y - other_pos.y) / distance
