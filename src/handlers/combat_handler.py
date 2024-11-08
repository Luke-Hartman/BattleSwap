"""Combat handler module for Battle Swap.

This module contains the CombatHandler class, which is responsible for
handling attack/skill/AoE/etc logic and applying damage/healing from attacks/skills/AoEs/etc.
"""

from typing import Optional
import esper
import math
from components import team
from components.animation import AnimationState, AnimationType
from components.aoe import AoE, DamageAoE
from components.armor import Armor
from components.aura import AffectedByAuras, DamageBuffAura
from components.expiration import Expiration
from components.orientation import Orientation
from components.projectile import AoEProjectile, DamageProjectile, Projectile
from components.skill import CreateAoE, SelfHeal, Skill
from components.unit_state import UnitState, State
from components.attack import HealingAttack, MeleeAttack, ProjectileAttack
from components.health import Health
from components.position import Position
from components.team import Team
from components.velocity import Velocity
from entities.effects import create_healing_effect
from events import (
    AttackActivatedEvent, ATTACK_ACTIVATED, 
    KillingBlowEvent, KILLING_BLOW, 
    ProjectileHitEvent, PROJECTILE_HIT,
    SkillActivatedEvent, SKILL_ACTIVATED,
    AoEHitEvent, AOE_HIT,
    emit_event
)
from pydispatch import dispatcher
from visuals import create_visual_spritesheet

class CombatHandler:
    """Handler responsible for handling attack logic and applying damage."""

    def __init__(self):
        dispatcher.connect(self.handle_attack_activated, signal=ATTACK_ACTIVATED)
        dispatcher.connect(self.handle_projectile_hit, signal=PROJECTILE_HIT)
        dispatcher.connect(self.handle_skill_activated, signal=SKILL_ACTIVATED)
        dispatcher.connect(self.handle_aoe_hit, signal=AOE_HIT)

    def handle_attack_activated(self, event: AttackActivatedEvent):
        attacker = event.entity
        attacker_state = esper.component_for_entity(attacker, UnitState)
        
        if attacker_state.state != State.ATTACKING or attacker_state.target is None:
            return

        melee_attack = esper.try_component(attacker, MeleeAttack)
        if melee_attack:
            self.handle_melee_attack(attacker, attacker_state.target, melee_attack)
            return
        projectile_attack = esper.try_component(attacker, ProjectileAttack)
        if projectile_attack:
            self.handle_projectile_attack(attacker, attacker_state.target, projectile_attack)
            return
        healing_attack = esper.try_component(attacker, HealingAttack)
        if healing_attack:
            self.handle_healing_attack(attacker, attacker_state.target, healing_attack)
            return
        raise AssertionError("Attack type not supported")

    def handle_skill_activated(self, event: SkillActivatedEvent):
        entity = event.entity
        skill = esper.component_for_entity(entity, Skill)
        if isinstance(skill.effect, SelfHeal):
            health = esper.component_for_entity(entity, Health)
            health.current = min(health.current + skill.effect.percent * health.maximum, health.maximum)
        elif isinstance(skill.effect, CreateAoE):
            position = esper.component_for_entity(entity, Position)
            team = esper.component_for_entity(entity, Team)
            orientation = esper.component_for_entity(entity, Orientation)
            aoe = esper.create_entity()
            esper.add_component(aoe, Position(x=position.x, y=position.y))
            esper.add_component(aoe, Team(type=team.type))
            esper.add_component(aoe, AoE(effect=skill.effect.effect, owner=entity, affected_entities=[entity]))
            esper.add_component(aoe, create_visual_spritesheet(skill.effect.visual, duration=skill.effect.duration, scale=skill.effect.scale))
            esper.add_component(aoe, AnimationState(type=AnimationType.IDLE))
            esper.add_component(aoe, Expiration(time_left=skill.effect.duration))
            esper.add_component(aoe, Orientation(facing=orientation.facing))
        else:
            raise ValueError(f"Skill effect {skill.effect} not supported")

    def handle_melee_attack(self, attacker: int, target: int, attack: MeleeAttack):
        damage = attack.damage
        self.deal_damage(attacker, target, damage)

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

        entity = esper.create_entity()
        esper.add_component(entity, Position(x=projectile_x, y=projectile_y))
        esper.add_component(entity, Velocity(x=velocity_x, y=velocity_y))
        esper.add_component(entity, Team(type=attacker_team.type))
        esper.add_component(entity, Projectile(effect=attack.projectile_effect, owner=attacker))
        esper.add_component(entity, create_visual_spritesheet(attack.visual))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))

    def handle_healing_attack(self, attacker: int, target: int, attack: HealingAttack):
        healing = attack.healing
        self.deal_healing(attacker, target, healing)
        create_healing_effect(target)

    def handle_projectile_hit(self, event: ProjectileHitEvent):
        projectile_ent = event.entity
        target_ent = event.target
        projectile = esper.component_for_entity(projectile_ent, Projectile)
        if isinstance(projectile.effect, DamageProjectile):
            self.deal_damage(
                attacker=projectile.owner,
                target=target_ent,
                base_damage=projectile.effect.damage
            )
        elif isinstance(projectile.effect, AoEProjectile):
            entity = esper.create_entity()
            position = esper.component_for_entity(projectile_ent, Position)
            team = esper.component_for_entity(projectile_ent, Team)
            esper.add_component(entity, Position(x=position.x, y=position.y))
            esper.add_component(entity, Team(type=team.type))
            esper.add_component(
                entity,
                AoE(effect=projectile.effect.effect, owner=projectile.owner)
            )
            esper.add_component(
                entity,
                create_visual_spritesheet(
                    visual=projectile.effect.visual,
                    scale=projectile.effect.scale,
                    duration=projectile.effect.duration
                )
            )
            esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
            esper.add_component(entity, Expiration(time_left=projectile.effect.duration))

    def handle_aoe_hit(self, event: AoEHitEvent):
        aoe_ent = event.aoe
        target_ent = event.target
        aoe = esper.component_for_entity(aoe_ent, AoE)
        if target_ent in aoe.affected_entities:
            return
        aoe_team = esper.component_for_entity(aoe_ent, Team)
        target_team = esper.component_for_entity(target_ent, Team)
        ally = aoe_team.type == target_team.type
        if (
            aoe.effect.affects_allies and ally or
            aoe.effect.affects_enemies and not ally
        ):
            aoe.affected_entities.append(target_ent)
            if isinstance(aoe.effect, DamageAoE):
                self.deal_damage(
                    attacker=aoe.owner,
                    target=target_ent,
                    base_damage=aoe.effect.damage
                )

    def deal_damage(self, attacker: Optional[int], target: int, base_damage: int):
        # Apply buffs/debuffs from the attacker to the damage
        if attacker and esper.entity_exists(attacker):
            affected_by_auras = esper.component_for_entity(attacker, AffectedByAuras)
            for effect in affected_by_auras.effects:
                if isinstance(effect, DamageBuffAura):
                    base_damage *= 1 + effect.damage_percentage

        # Apply armor to the damage
        target_health = esper.component_for_entity(target, Health)
        target_armor = esper.try_component(target, Armor)
        if target_armor:
            base_damage = target_armor.calculate_damage_after_armor(base_damage)
        if target_health is None:
            raise AssertionError("Target has no health component")

        # Apply the damage
        previous_health = target_health.current
        target_health.current = max(target_health.current - base_damage, 0)
        if target_health.current == 0 and previous_health > 0:
            emit_event(KILLING_BLOW, event=KillingBlowEvent(target))

    def deal_healing(self, attacker: Optional[int], target: int, healing: int):
        target_health = esper.component_for_entity(target, Health)
        target_health.current = min(target_health.current + healing, target_health.maximum)
