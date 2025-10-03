import esper

from components.unit_state import State, UnitState
from components.velocity import Velocity
from components.corpse_timer import CorpseTimer

class DeadProcessor(esper.Processor):
    def process(self, dt: float):
        for ent, (unit_state, velocity) in esper.get_components(UnitState, Velocity):
            if unit_state.state == State.DEAD:
                velocity.x = 0
                velocity.y = 0
                # Increment corpse timer
                corpse_timer = esper.component_for_entity(ent, CorpseTimer)
                corpse_timer.time_dead += dt
