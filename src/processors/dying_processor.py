"""Processor for units that are dying."""

import esper
from components.dying import Dying
from events import DEATH, DeathEvent, emit_event

class DyingProcessor(esper.Processor):
    """Processor for units that are dying."""

    def process(self, dt: float):
        for ent, (dying,) in esper.get_components(Dying):
            emit_event(DEATH, event=DeathEvent(ent))
            esper.remove_component(ent, Dying)

