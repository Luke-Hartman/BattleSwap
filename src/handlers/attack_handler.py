"""Attack handler module for Battle Swap.

This module contains the AttackHandler class, which is responsible for
handling attack logic and applying damage.
"""

import esper
from components.unit_state import UnitState, State
from components.attack import MeleeAttack
from components.health import Health
from components.position import Position
from events import AttackActivatedEvent, ATTACK_ACTIVATED
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
        target_health.current -= melee_attack.damage
        if target_health.current < 0:
            target_health.current = 0
            # Here you might want to trigger a death event or change the target's state
