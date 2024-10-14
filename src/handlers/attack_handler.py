"""Attack handler module for Battle Swap.

This module contains the AttackHandler class, which is responsible for
handling attack logic and applying damage.
"""

import esper
from components.unit_state import UnitState, State
from components.attack import MeleeAttack
from components.health import Health
from events import AttackActivatedEvent, ATTACK_ACTIVATED, KillingBlowEvent, KILLING_BLOW, emit_event
from pydispatch import dispatcher

class AttackHandler:
    """Handler responsible for handling attack logic and applying damage."""

    def __init__(self):
        dispatcher.connect(self.handle_attack_activated, signal=ATTACK_ACTIVATED)

    def handle_attack_activated(self, event: AttackActivatedEvent):
        attacker = event.entity
        attacker_state = esper.component_for_entity(attacker, UnitState)
        
        if attacker_state.state != State.ATTACKING or attacker_state.target is None:
            return

        melee_attack = esper.try_component(attacker, MeleeAttack)
        if melee_attack is None:
            return  # This is not a melee attacker

        target = attacker_state.target
        target_health = esper.try_component(target, Health)
        if target_health is None:
            raise AssertionError("Target has no health component")

        # Assume target is still in range
        previous_health = target_health.current
        target_health.current = max(target_health.current - melee_attack.damage, 0)
        if target_health.current == 0 and previous_health > 0:
            emit_event(KILLING_BLOW, event=KillingBlowEvent(target))
