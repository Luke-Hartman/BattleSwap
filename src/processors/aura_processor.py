"""Processor for aura effects."""

import esper
from components.aura import Auras
from components.position import Position
from events import AURA_HIT, AuraHitEvent, emit_event


class AuraProcessor(esper.Processor):
    """Processor for aura effects."""

    def process(self, dt: float):
        for ent, (auras, position) in esper.get_components(Auras, Position):
            active_auras = []
            for aura in auras.auras:
                if aura.time_elapsed % aura.period < dt and aura.owner_condition.check(aura.owner):
                    for other_ent, (other_position,) in esper.get_components(Position):
                        if position.distance(other_position, y_bias=None) <= aura.radius:
                            emit_event(AURA_HIT, event=AuraHitEvent(entity=ent, target=other_ent, aura=aura))
                aura.time_elapsed += dt
                if aura.time_elapsed <= aura.duration:
                    active_auras.append(aura)
            auras.auras = active_auras