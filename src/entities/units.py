"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import esper
import pygame
import os
from typing import Dict
from CONSTANTS import *
from components.armor import Armor
from components.aura import AffectedByAuras, Aura, DamageBuffAura
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.skill import SelfHeal, Skill, UnderHealthPercent
from components.sprite_sheet import SpriteSheet
from components.targetting_strategy import TargettingStrategyComponent, TargettingStrategyType
from components.team import Team, TeamType
from components.unit_state import UnitState
from components.attack import HealingAttack, MeleeAttack, ProjectileAttack, ProjectileType
from components.movement import Movement
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection

unit_theme_ids: Dict[UnitType, str] = {
    UnitType.CORE_ARCHER: "#core_archer_icon", 
    UnitType.CORE_DUELIST: "#core_duelist_icon",
    UnitType.CORE_HORSEMAN: "#core_horseman_icon",
    UnitType.CORE_MAGE: "#core_mage_icon",
    UnitType.CORE_SWORDSMAN: "#core_swordsman_icon",
    UnitType.CRUSADER_BLACK_KNIGHT: "#crusader_black_knight_icon",
    UnitType.CRUSADER_CLERIC: "#crusader_cleric_icon",
    UnitType.CRUSADER_COMMANDER: "#crusader_commander_icon",
    UnitType.CRUSADER_DEFENDER: "#crusader_defender_icon",
    UnitType.CRUSADER_GOLD_KNIGHT: "#crusader_gold_knight_icon",
    UnitType.CRUSADER_LONGBOWMAN: "#crusader_longbowman_icon",
    UnitType.CRUSADER_PALADIN: "#crusader_paladin_icon",
    UnitType.CRUSADER_PIKEMAN: "#crusader_pikeman_icon",
    UnitType.WEREBEAR: "#werebear_icon",
}

unit_icon_surfaces: Dict[UnitType, pygame.Surface] = {}

sprite_sheets: Dict[TeamType, Dict[UnitType, pygame.Surface]] = {
    TeamType.TEAM1: {},
    TeamType.TEAM2: {}
}

def load_sprite_sheets():
    """Load all sprite sheets and unit icons."""
    unit_filenames = {
        UnitType.CORE_ARCHER: "CoreArcher.png", 
        UnitType.CORE_DUELIST: "CoreDuelist.png",
        UnitType.CORE_HORSEMAN: "CoreHorseman.png",
        UnitType.CORE_MAGE: "CoreMage.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsman.png", 
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnight.png",
        UnitType.CRUSADER_CLERIC: "CrusaderCleric.png",
        UnitType.CRUSADER_COMMANDER: "CrusaderCommander.png",
        UnitType.CRUSADER_DEFENDER: "CrusaderDefender.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnight.png",
        UnitType.CRUSADER_LONGBOWMAN: "CrusaderLongbowman.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladin.png",
        UnitType.CRUSADER_PIKEMAN: "CrusaderPikeman.png",
        UnitType.WEREBEAR: "Werebear.png",
    }
    for unit_type, filename in unit_filenames.items():
        path = os.path.join("assets", "units", filename)
        sprite_sheets[unit_type] = pygame.image.load(path).convert_alpha()

    # Load unit icons
    unit_icon_paths: Dict[UnitType, str] = {
        UnitType.CORE_ARCHER: "CoreArcherIcon.png",
        UnitType.CORE_DUELIST: "CoreDuelistIcon.png",
        UnitType.CORE_HORSEMAN: "CoreHorsemanIcon.png",
        UnitType.CORE_MAGE: "CoreMageIcon.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsmanIcon.png",
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnightIcon.png",
        UnitType.CRUSADER_CLERIC: "CrusaderClericIcon.png",
        UnitType.CRUSADER_COMMANDER: "CrusaderCommanderIcon.png",
        UnitType.CRUSADER_DEFENDER: "CrusaderDefenderIcon.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnightIcon.png",
        UnitType.CRUSADER_LONGBOWMAN: "CrusaderLongbowmanIcon.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladinIcon.png",
        UnitType.CRUSADER_PIKEMAN: "CrusaderPikemanIcon.png",
        UnitType.WEREBEAR: "WerebearIcon.png",
    }
    for unit_type, filename in unit_icon_paths.items():
        path = os.path.join("assets", "icons", filename)
        unit_icon_surfaces[unit_type] = pygame.image.load(path).convert_alpha()

def create_unit(x: int, y: int, unit_type: UnitType, team: TeamType) -> int:
    """Create a unit entity with all necessary components."""
    return {
        UnitType.CORE_ARCHER: create_core_archer,
        UnitType.CORE_DUELIST: create_core_duelist,
        UnitType.CORE_HORSEMAN: create_core_horseman,
        UnitType.CORE_MAGE: create_core_mage,
        UnitType.CORE_SWORDSMAN: create_core_swordsman,
        UnitType.CRUSADER_BLACK_KNIGHT: create_crusader_black_knight,
        UnitType.CRUSADER_CLERIC: create_crusader_cleric,
        UnitType.CRUSADER_COMMANDER: create_crusader_commander,
        UnitType.CRUSADER_DEFENDER: create_crusader_defender,
        UnitType.CRUSADER_GOLD_KNIGHT: create_crusader_gold_knight,
        UnitType.CRUSADER_LONGBOWMAN: create_crusader_longbowman,
        UnitType.CRUSADER_PALADIN: create_crusader_paladin,
        UnitType.CRUSADER_PIKEMAN: create_crusader_pikeman,
        UnitType.WEREBEAR: create_werebear,
    }[unit_type](x, y, team)


def unit_base_entity(
        x: int,
        y: int,
        team: TeamType,
        unit_type: UnitType,
        movement_speed: float,
        health: int,
    ) -> int:
    """Create a unit entity with all components shared by all units."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, Movement(speed=movement_speed))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=unit_type))
    esper.add_component(entity, Health(current=health, maximum=health))
    esper.add_component(entity, AffectedByAuras())
    esper.add_component(entity, get_unit_sprite_sheet(unit_type))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_core_archer(x: int, y: int, team: TeamType) -> int:
    """Create an archer entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CORE_ARCHER, CORE_ARCHER_MOVEMENT_SPEED, CORE_ARCHER_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(
        entity,
        ProjectileAttack(
            range=CORE_ARCHER_ATTACK_RANGE,
            damage=CORE_ARCHER_ATTACK_DAMAGE,
            projectile_speed=CORE_ARCHER_PROJECTILE_SPEED,
            projectile_type=ProjectileType.ARROW,
            projectile_offset_x=5*MINIFOLKS_SCALE,
            projectile_offset_y=0,
        )
    )
    return entity

def create_core_duelist(x: int, y: int, team: TeamType) -> int:
    """Create a fancy swordsman entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CORE_DUELIST, CORE_DUELIST_MOVEMENT_SPEED, CORE_DUELIST_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CORE_DUELIST_ATTACK_RANGE, damage=CORE_DUELIST_ATTACK_DAMAGE))
    return entity

def create_core_horseman(x: int, y: int, team: TeamType) -> int:
    """Create a horseman entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CORE_HORSEMAN, CORE_HORSEMAN_MOVEMENT_SPEED, CORE_HORSEMAN_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CORE_HORSEMAN_ATTACK_RANGE, damage=CORE_HORSEMAN_ATTACK_DAMAGE))
    return entity

def create_core_mage(x: int, y: int, team: TeamType) -> int:
    """Create a mage entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CORE_MAGE, CORE_MAGE_MOVEMENT_SPEED, CORE_MAGE_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(
        entity,
        ProjectileAttack(
            range=CORE_MAGE_ATTACK_RANGE,
            damage=CORE_MAGE_ATTACK_DAMAGE,
            projectile_speed=CORE_MAGE_PROJECTILE_SPEED,
            projectile_type=ProjectileType.FIREBALL,
            projectile_offset_x=11*MINIFOLKS_SCALE,
            projectile_offset_y=-4*MINIFOLKS_SCALE,
        )
    )
    return entity

def create_core_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a swordsman entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CORE_SWORDSMAN, CORE_SWORDSMAN_MOVEMENT_SPEED, CORE_SWORDSMAN_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CORE_SWORDSMAN_ATTACK_RANGE, damage=CORE_SWORDSMAN_ATTACK_DAMAGE))
    return entity

def create_crusader_black_knight(x: int, y: int, team: TeamType) -> int:
    """Create a black knight entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_BLACK_KNIGHT, CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED, CRUSADER_BLACK_KNIGHT_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CRUSADER_BLACK_KNIGHT_ATTACK_RANGE, damage=CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE))
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_BLACK_KNIGHT_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_BLACK_KNIGHT_ARMOR_PERCENT_REDUCTION))
    esper.add_component(entity, Aura(
        radius=CRUSADER_BLACK_KNIGHT_AURA_RADIUS,
        effect=DamageBuffAura( # Debuffs enemy damage
            key="CRUSADER_BLACK_KNIGHT_AURA",
            damage_percentage=-CRUSADER_BLACK_KNIGHT_AURA_DAMAGE_PERCENT_REDUCTION,
            affects_enemies=True,
            affects_melee=True,
            affects_ranged=True,
            affects_healing=False,
        ),
        color=(150, 0, 0)
    ))
    return entity

def create_crusader_cleric(x: int, y: int, team: TeamType) -> int:
    """Create a cleric entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_CLERIC, CRUSADER_CLERIC_MOVEMENT_SPEED, CRUSADER_CLERIC_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.STRONGEST_ALLY))
    esper.add_component(entity, HealingAttack(range=CRUSADER_CLERIC_ATTACK_RANGE, healing=CRUSADER_CLERIC_HEALING))
    return entity

def create_crusader_commander(x: int, y: int, team: TeamType) -> int:
    """Create a commander entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_COMMANDER, CRUSADER_COMMANDER_MOVEMENT_SPEED, CRUSADER_COMMANDER_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CRUSADER_COMMANDER_ATTACK_RANGE, damage=CRUSADER_COMMANDER_ATTACK_DAMAGE))
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_COMMANDER_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_COMMANDER_ARMOR_PERCENT_REDUCTION))
    return entity

def create_crusader_defender(x: int, y: int, team: TeamType) -> int:
    """Create a defender entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_DEFENDER, CRUSADER_DEFENDER_MOVEMENT_SPEED, CRUSADER_DEFENDER_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CRUSADER_DEFENDER_ATTACK_RANGE, damage=CRUSADER_DEFENDER_ATTACK_DAMAGE))
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_DEFENDER_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_DEFENDER_ARMOR_PERCENT_REDUCTION))
    return entity

def create_crusader_gold_knight(x: int, y: int, team: TeamType) -> int:
    """Create a gold knight entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_GOLD_KNIGHT, CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED, CRUSADER_GOLD_KNIGHT_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CRUSADER_GOLD_KNIGHT_ATTACK_RANGE, damage=CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE))
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_GOLD_KNIGHT_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_GOLD_KNIGHT_ARMOR_PERCENT_REDUCTION))
    esper.add_component(entity, Aura(
        radius=CRUSADER_GOLD_KNIGHT_AURA_RADIUS,
        effect=DamageBuffAura( # Buffs ally melee damage, excluding self
            key="CRUSADER_GOLD_KNIGHT_AURA",
            damage_percentage=CRUSADER_GOLD_KNIGHT_AURA_DAMAGE_PERCENT_BUFF,
            affects_allies=True,
            affects_melee=True,
            affects_self=False,
        ),
        color=(255, 215, 0)
    ))
    return entity

def create_crusader_longbowman(x: int, y: int, team: TeamType) -> int:
    """Create a longbowman entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_LONGBOWMAN, CRUSADER_LONGBOWMAN_MOVEMENT_SPEED, CRUSADER_LONGBOWMAN_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(
        entity,
        ProjectileAttack(
            range=CRUSADER_LONGBOWMAN_ATTACK_RANGE,
            damage=CRUSADER_LONGBOWMAN_ATTACK_DAMAGE,
            projectile_speed=CRUSADER_LONGBOWMAN_PROJECTILE_SPEED,
            projectile_type=ProjectileType.ARROW,
            projectile_offset_x=5*MINIFOLKS_SCALE,
            projectile_offset_y=0
        )
    )
    return entity

def create_crusader_paladin(x: int, y: int, team: TeamType) -> int:
    """Create a paladin entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_PALADIN, CRUSADER_PALADIN_MOVEMENT_SPEED, CRUSADER_PALADIN_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CRUSADER_PALADIN_ATTACK_RANGE, damage=CRUSADER_PALADIN_ATTACK_DAMAGE))
    esper.add_component(
        entity,
        Skill(
            trigger_condition=UnderHealthPercent(percent=CRUSADER_PALADIN_SKILL_HEALTH_PERCENT_THRESHOLD),
            effect=SelfHeal(percent=CRUSADER_PALADIN_SKILL_HEAL_PERCENT),
            cooldown=CRUSADER_PALADIN_SKILL_COOLDOWN
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_PALADIN_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_PALADIN_ARMOR_PERCENT_REDUCTION))
    return entity

def create_crusader_pikeman(x: int, y: int, team: TeamType) -> int:
    """Create a pikeman entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.CRUSADER_PIKEMAN, CRUSADER_PIKEMAN_MOVEMENT_SPEED, CRUSADER_PIKEMAN_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=CRUSADER_PIKEMAN_ATTACK_RANGE, damage=CRUSADER_PIKEMAN_ATTACK_DAMAGE))
    return entity

def create_werebear(x: int, y: int, team: TeamType) -> int:
    """Create a werebear entity with all necessary components."""
    entity = unit_base_entity(x, y, team, UnitType.WEREBEAR, WEREBEAR_MOVEMENT_SPEED, WEREBEAR_HP)
    esper.add_component(entity, TargettingStrategyComponent(type=TargettingStrategyType.NEAREST_ENEMY))
    esper.add_component(entity, MeleeAttack(range=WEREBEAR_ATTACK_RANGE, damage=WEREBEAR_ATTACK_DAMAGE))
    return entity

def get_unit_sprite_sheet(unit_type: UnitType) -> SpriteSheet:
    """Get a SpriteSheet component for a unit type.

    Args:
        unit_type: The type of unit to get sprite sheet for.
        team: The team the unit belongs to.
        
    Returns:
        SpriteSheet component configured for the unit type.
    """
    if unit_type == UnitType.CORE_ARCHER:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
            animation_durations=CORE_ARCHER_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=7
        )
    elif unit_type == UnitType.CORE_DUELIST:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 12, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 6},
            animation_durations=CORE_DUELIST_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=5
        )
    elif unit_type == UnitType.CORE_HORSEMAN:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 8, AnimationType.WALKING: 6, AnimationType.ATTACKING: 7, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 6},
            animation_durations=CORE_HORSEMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=3
        )
    elif unit_type == UnitType.CORE_MAGE:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 9},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 7},
            animation_durations=CORE_MAGE_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=7
        )
    elif unit_type == UnitType.CORE_SWORDSMAN:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 5},
            animation_durations=CORE_SWORDSMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=2
        )
    elif unit_type == UnitType.CRUSADER_BLACK_KNIGHT:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
            animation_durations=CRUSADER_BLACK_KNIGHT_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=3
        )
    elif unit_type == UnitType.CRUSADER_CLERIC:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 7},
            animation_durations=CRUSADER_CLERIC_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=2
        )
    elif unit_type == UnitType.CRUSADER_COMMANDER:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 7, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 8},
            animation_durations=CRUSADER_COMMANDER_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=4
        )
    elif unit_type == UnitType.CRUSADER_DEFENDER:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
            animation_durations=CRUSADER_DEFENDER_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=4
        )
    elif unit_type == UnitType.CRUSADER_GOLD_KNIGHT:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 9, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 2, AnimationType.DYING: 5},
            animation_durations=CRUSADER_GOLD_KNIGHT_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=4
        )
    elif unit_type == UnitType.CRUSADER_LONGBOWMAN:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ATTACKING: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 2, AnimationType.DYING: 5},
            animation_durations=CRUSADER_LONGBOWMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=6
        )
    elif unit_type == UnitType.CRUSADER_PALADIN:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 6, AnimationType.SKILL: 13, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.SKILL: 7, AnimationType.DYING: 6},
            animation_durations=CRUSADER_PALADIN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=3,
            skill_activation_frame=9
        )
    elif unit_type == UnitType.CRUSADER_PIKEMAN:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=68,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 5, AnimationType.ATTACKING: 7, AnimationType.DYING: 7},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 2, AnimationType.DYING: 3},
            animation_durations=CRUSADER_PIKEMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(24, -16),
            attack_activation_frame=3
        )
    elif unit_type == UnitType.WEREBEAR:
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ATTACKING: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 2, AnimationType.DYING: 6},
            animation_durations=WEREBEAR_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=5
        )
    else:
        raise ValueError(f"Unknown unit type: {unit_type}")

