"""Processor for aura effects."""

import time
import esper
from components.aura import Aura
from components.position import Position
from events import AURA_HIT, AuraHitEvent, emit_event


class AuraProcessor(esper.Processor):
    """Processor for aura effects."""

    def process(self, dt: float):
        for ent, (aura, position) in esper.get_components(Aura, Position):
            current_time = time.time()
            time_since_last_triggered = current_time - aura.last_triggered
            if time_since_last_triggered < aura.period:
                continue
            aura.last_triggered = current_time
            for other_ent, (other_position,) in esper.get_components(Position):
                if position.distance(other_position, y_bias=None) <= aura.radius:
                    emit_event(AURA_HIT, event=AuraHitEvent(entity=ent, target=other_ent))
