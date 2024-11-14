import esper

from components.unit_state import State, UnitState
from components.velocity import Velocity

class DeadProcessor(esper.Processor):
    def process(self, dt: float):
        for ent, (unit_state, velocity) in esper.get_components(UnitState, Velocity):
            if unit_state.state == State.DEAD:
                velocity.x = 0
                velocity.y = 0
