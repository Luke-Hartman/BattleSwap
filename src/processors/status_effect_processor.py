"""Processor for status effects."""

from components.health import Health
from components.status_effect import CrusaderBlackKnightDebuffed, CrusaderCommanderEmpowered, Ignited, StatusEffects
import esper

from events import KILLING_BLOW, KillingBlowEvent, emit_event

class StatusEffectProcessor(esper.Processor):
    """Processor for status effects."""

    def process(self, dt: float):
        for ent, (status_effects,) in esper.get_components(StatusEffects):
            for status_effect in status_effects.active_effects():
                if isinstance(status_effect, Ignited):
                    damage = status_effect.dps * dt
                    health = esper.component_for_entity(ent, Health)
                    health.current = max(health.current - damage, 0)
                    if health.current == 0:
                        emit_event(KILLING_BLOW, event=KillingBlowEvent(entity=ent))
                elif isinstance(status_effect, CrusaderCommanderEmpowered):
                    pass
                elif isinstance(status_effect, CrusaderBlackKnightDebuffed):
                    pass
                else:
                    raise ValueError(f"Unknown status effect: {status_effect}")
