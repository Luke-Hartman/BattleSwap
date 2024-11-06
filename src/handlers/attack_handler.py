"""Attack handler module for Battle Swap.

This module contains the AttackHandler class, which is responsible for
handling attack logic and applying damage from attacks.
"""

import esper
import math
from components.armor import Armor
from components.orientation import Orientation
from components.unit_state import UnitState, State
from components.attack import MeleeAttack, ProjectileAttack, ProjectileType
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
from entities.projectiles import create_arrow, create_fireball

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
        attacker_orientation = esper.component_for_entity(attacker, Orientation)
        projectile_x = attacker_pos.x + attack.projectile_offset_x * attacker_orientation.facing.value
        projectile_y = attacker_pos.y + attack.projectile_offset_y
        target_pos = esper.component_for_entity(target, Position)
        attacker_team = esper.component_for_entity(attacker, Team)

        dx = target_pos.x - projectile_x
        dy = target_pos.y - projectile_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            velocity_x = (dx / distance) * attack.projectile_speed
            velocity_y = (dy / distance) * attack.projectile_speed
        else:
            velocity_x = attack.projectile_speed
            velocity_y = 0
        if attack.projectile_type == ProjectileType.ARROW:
            create_arrow(
                x=projectile_x,
                y=projectile_y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                team=attacker_team.type,
                damage=attack.damage,
            )
        elif attack.projectile_type == ProjectileType.FIREBALL:
            create_fireball(
                x=projectile_x,
                y=projectile_y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                team=attacker_team.type,
                damage=attack.damage,
            )

    def handle_projectile_hit(self, event: ProjectileHitEvent):
        self.deal_damage(event.target, event.damage)

    def deal_damage(self, target: int, damage: int):
        target_health = esper.component_for_entity(target, Health)
        target_armor = esper.try_component(target, Armor)
        if target_armor:
            damage = target_armor.calculate_damage_after_armor(damage)
        if target_health is None:
            raise AssertionError("Target has no health component")

        previous_health = target_health.current
        target_health.current = max(target_health.current - damage, 0)
        if target_health.current == 0 and previous_health > 0:
            emit_event(KILLING_BLOW, event=KillingBlowEvent(target))
