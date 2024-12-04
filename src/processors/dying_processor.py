"""Processor for units that are dying."""

import esper
from components.dying import Dying
from components.unit_type import UnitTypeComponent
from events import DEATH, DeathEvent, emit_event
from voice import play_death

class DyingProcessor(esper.Processor):
    """Processor for units that are dying."""

    def process(self, dt: float):
        for ent, (dying, unit_type) in esper.get_components(Dying, UnitTypeComponent):
            emit_event(DEATH, event=DeathEvent(ent))
            play_death(unit_type.type)
            esper.remove_component(ent, Dying)
