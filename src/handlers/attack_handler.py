"""Attack handler module for Battle Swap.

This module contains the AttackHandler class, which is responsible for
handling attack logic and applying damage.
"""

import esper
import math
from components.unit_state import UnitState, State
from components.attack import MeleeAttack, ProjectileAttack
from components.health import Health
from components.position import Position
from components.team import Team
from events import (
    AttackActivatedEvent, ATTACK_ACTIVATED, 
    KillingBlowEvent, KILLING_BLOW, 
    ProjectileHitEvent, PROJECTILE_HIT,
    emit_event
)
from pydispatch import dispatcher
from entities.projectiles import create_arrow

class AttackHandler:
    """Handler responsible for handling attack logic and applying damage."""

    def __init__(self):
        dispatcher.connect(self.handle_attack_activated, signal=ATTACK_ACTIVATED)
        dispatcher.connect(self.handle_projectile_hit, signal=PROJECTILE_HIT)

    def handle_attack_activated(self, event: AttackActivatedEvent):
        attacker = event.entity
        attacker_state = esper.component_for_entity(attacker, UnitState)
        
        if attacker_state.state != State.ATTACKING or attacker_state.target is None:
            return

        melee_attack = esper.try_component(attacker, MeleeAttack)
        if melee_attack:
            self.handle_melee_attack(attacker, attacker_state.target, melee_attack)
        else:
            projectile_attack = esper.try_component(attacker, ProjectileAttack)
            if projectile_attack:
                self.handle_projectile_attack(attacker, attacker_state.target, projectile_attack)

    def handle_melee_attack(self, attacker: int, target: int, attack: MeleeAttack):
        self.deal_damage(target, attack.damage)

    def handle_projectile_attack(self, attacker: int, target: int, attack: ProjectileAttack):
        attacker_pos = esper.component_for_entity(attacker, Position)
        target_pos = esper.component_for_entity(target, Position)
        attacker_team = esper.component_for_entity(attacker, Team)

        dx = target_pos.x - attacker_pos.x
        dy = target_pos.y - attacker_pos.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            velocity_x = (dx / distance) * attack.projectile_speed
            velocity_y = (dy / distance) * attack.projectile_speed
        else:
            velocity_x = attack.projectile_speed
            velocity_y = 0

        create_arrow(attacker_pos.x, attacker_pos.y, velocity_x, velocity_y, attacker_team.type, attack.damage)

    def handle_projectile_hit(self, event: ProjectileHitEvent):
        self.deal_damage(event.target, event.damage)

    def deal_damage(self, target: int, damage: int):
        target_health = esper.component_for_entity(target, Health)
        if target_health is None:
            raise AssertionError("Target has no health component")

        previous_health = target_health.current
        target_health.current = max(target_health.current - damage, 0)
        if target_health.current == 0 and previous_health > 0:
            emit_event(KILLING_BLOW, event=KillingBlowEvent(target))
