"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import esper
import pygame
import os
from typing import Dict
from CONSTANTS import (
    MINIFOLKS_SCALE,
    SWORDSMAN_HP, SWORDSMAN_ATTACK_RANGE, SWORDSMAN_ATTACK_DAMAGE, SWORDSMAN_MOVEMENT_SPEED, SWORDSMAN_ANIMATION_DURATIONS,
    ARCHER_HP, ARCHER_ATTACK_RANGE, ARCHER_ATTACK_DAMAGE, ARCHER_MOVEMENT_SPEED, ARCHER_PROJECTILE_SPEED, ARCHER_ANIMATION_DURATIONS,
    MAGE_HP, MAGE_ATTACK_RANGE, MAGE_ATTACK_DAMAGE, MAGE_MOVEMENT_SPEED, MAGE_PROJECTILE_SPEED, MAGE_ANIMATION_DURATIONS,
    HORSEMAN_HP, HORSEMAN_ATTACK_RANGE, HORSEMAN_ATTACK_DAMAGE, HORSEMAN_MOVEMENT_SPEED, HORSEMAN_ANIMATION_DURATIONS,
    TINY_RPG_SCALE,
    WEREBEAR_HP, WEREBEAR_ATTACK_RANGE, WEREBEAR_ATTACK_DAMAGE, WEREBEAR_MOVEMENT_SPEED, WEREBEAR_ANIMATION_DURATIONS,
    FANCY_SWORDSMAN_HP, FANCY_SWORDSMAN_ATTACK_RANGE, FANCY_SWORDSMAN_ATTACK_DAMAGE, FANCY_SWORDSMAN_MOVEMENT_SPEED, FANCY_SWORDSMAN_ANIMATION_DURATIONS
)
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState
from components.attack import MeleeAttack, ProjectileAttack, ProjectileType
from components.movement import Movement
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection

unit_theme_ids: Dict[UnitType, str] = {
    UnitType.SWORDSMAN: "#swordman_icon",
    UnitType.ARCHER: "#archer_icon", 
    UnitType.MAGE: "#mage_icon",
    UnitType.HORSEMAN: "#horseman_icon",
    UnitType.WEREBEAR: "#werebear_icon",
    UnitType.FANCY_SWORDSMAN: "#fancy_swordsman_icon"
}

unit_icon_surfaces: Dict[UnitType, pygame.Surface] = {}

sprite_sheets: Dict[TeamType, Dict[UnitType, pygame.Surface]] = {
    TeamType.TEAM1: {},
    TeamType.TEAM2: {}
}

def load_sprite_sheets():
    """Load all sprite sheets and unit icons."""
    # Load sprite sheets as before
    team_colors = {TeamType.TEAM1: "Blue", TeamType.TEAM2: "Blue"}
    unit_filenames = {
        UnitType.SWORDSMAN: "MiniSwordMan.png", 
        UnitType.ARCHER: "MiniArcherMan.png", 
        UnitType.MAGE: "MiniMage.png",
        UnitType.HORSEMAN: "MiniHorseman.png",
        UnitType.WEREBEAR: "Werebear.png",
        UnitType.FANCY_SWORDSMAN: "Swordsman.png"
    }

    for team, color in team_colors.items():
        for unit_type, filename in unit_filenames.items():
            path = os.path.join("assets", color, filename)
            sprite_sheets[team][unit_type] = pygame.image.load(path).convert_alpha()
    
    # Load unit icons
    unit_icon_paths: Dict[UnitType, str] = {
        UnitType.SWORDSMAN: "MiniSwordManIcon.png",
        UnitType.ARCHER: "MiniArcherIcon.png",
        UnitType.MAGE: "MiniMageIcon.png",
        UnitType.HORSEMAN: "MiniHorseManIcon.png",
        UnitType.WEREBEAR: "WerebearIcon.png",
        UnitType.FANCY_SWORDSMAN: "FancySwordsmanIcon.png"
    }
    for unit_type, filename in unit_icon_paths.items():
        path = os.path.join("assets", "icons", filename)
        unit_icon_surfaces[unit_type] = pygame.image.load(path).convert_alpha()

def create_unit(x: int, y: int, unit_type: UnitType, team: TeamType) -> int:
    """Create a unit entity with all necessary components."""
    return {
        UnitType.SWORDSMAN: create_swordsman,
        UnitType.ARCHER: create_archer,
        UnitType.MAGE: create_mage,
        UnitType.HORSEMAN: create_horseman,
        UnitType.WEREBEAR: create_werebear,
        UnitType.FANCY_SWORDSMAN: create_fancy_swordsman,
    }[unit_type](x, y, team)

def create_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a swordsman entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=UnitType.SWORDSMAN))
    esper.add_component(entity, MeleeAttack(range=SWORDSMAN_ATTACK_RANGE, damage=SWORDSMAN_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=SWORDSMAN_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.SWORDSMAN, team))
    esper.add_component(entity, Health(current=SWORDSMAN_HP, maximum=SWORDSMAN_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_archer(x: int, y: int, team: TeamType) -> int:
    """Create an archer entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=UnitType.ARCHER))
    esper.add_component(
        entity,
        ProjectileAttack(
            range=ARCHER_ATTACK_RANGE,
            damage=ARCHER_ATTACK_DAMAGE,
            projectile_speed=ARCHER_PROJECTILE_SPEED,
            projectile_type=ProjectileType.ARROW,
            projectile_offset_x=5*MINIFOLKS_SCALE,
            projectile_offset_y=0,
        )
    )
    esper.add_component(entity, Movement(speed=ARCHER_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ARCHER, team))
    esper.add_component(entity, Health(current=ARCHER_HP, maximum=ARCHER_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_mage(x: int, y: int, team: TeamType) -> int:
    """Create a mage entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=UnitType.MAGE))
    esper.add_component(
        entity,
        ProjectileAttack(
            range=MAGE_ATTACK_RANGE,
            damage=MAGE_ATTACK_DAMAGE,
            projectile_speed=MAGE_PROJECTILE_SPEED,
            projectile_type=ProjectileType.FIREBALL,
            projectile_offset_x=11*MINIFOLKS_SCALE,
            projectile_offset_y=-4*MINIFOLKS_SCALE,
        )
    )
    esper.add_component(entity, Movement(speed=MAGE_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.MAGE, team))
    esper.add_component(entity, Health(current=MAGE_HP, maximum=MAGE_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_horseman(x: int, y: int, team: TeamType) -> int:
    """Create a horseman entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=UnitType.HORSEMAN))
    esper.add_component(entity, MeleeAttack(range=HORSEMAN_ATTACK_RANGE, damage=HORSEMAN_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=HORSEMAN_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.HORSEMAN, team))
    esper.add_component(entity, Health(current=HORSEMAN_HP, maximum=HORSEMAN_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_werebear(x: int, y: int, team: TeamType) -> int:
    """Create a werebear entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=UnitType.WEREBEAR))
    esper.add_component(entity, MeleeAttack(range=WEREBEAR_ATTACK_RANGE, damage=WEREBEAR_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=WEREBEAR_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.WEREBEAR, team))
    esper.add_component(entity, Health(current=WEREBEAR_HP, maximum=WEREBEAR_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_fancy_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a fancy swordsman entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=UnitType.FANCY_SWORDSMAN))
    esper.add_component(entity, MeleeAttack(range=FANCY_SWORDSMAN_ATTACK_RANGE, damage=FANCY_SWORDSMAN_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=FANCY_SWORDSMAN_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.FANCY_SWORDSMAN, team))
    esper.add_component(entity, Health(current=FANCY_SWORDSMAN_HP, maximum=FANCY_SWORDSMAN_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def get_unit_sprite_sheet(unit_type: UnitType, team: TeamType) -> SpriteSheet:
    """Get a SpriteSheet component for a unit type.
    
    Args:
        unit_type: The type of unit to get sprite sheet for.
        team: The team the unit belongs to.
        
    Returns:
        SpriteSheet component configured for the unit type.
    """
    if unit_type == UnitType.SWORDSMAN:
        return SpriteSheet(
            surface=sprite_sheets[team][unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 5},
            animation_durations=SWORDSMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=2
        )
    elif unit_type == UnitType.ARCHER:
        return SpriteSheet(
            surface=sprite_sheets[team][unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
            animation_durations=ARCHER_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=7
        )
    elif unit_type == UnitType.MAGE:
        return SpriteSheet(
            surface=sprite_sheets[team][unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 9},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 7},
            animation_durations=MAGE_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=7
        )
    elif unit_type == UnitType.HORSEMAN:
        return SpriteSheet(
            surface=sprite_sheets[team][unit_type],
            frame_width=32,
            frame_height=32,
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 8, AnimationType.WALKING: 6, AnimationType.ATTACKING: 7, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 6},
            animation_durations=HORSEMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, -8),
            attack_activation_frame=3
        )
    elif unit_type == UnitType.WEREBEAR:
        return SpriteSheet(
            surface=sprite_sheets[team][unit_type],
            frame_width=100,
            frame_height=100,
            scale=1.5*TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ATTACKING: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 2, AnimationType.DYING: 6},
            animation_durations=WEREBEAR_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=5
        )
    elif unit_type == UnitType.FANCY_SWORDSMAN:
        return SpriteSheet(
            surface=sprite_sheets[team][unit_type],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ATTACKING: 12, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 6},
            animation_durations=FANCY_SWORDSMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
            attack_activation_frame=5
        )

