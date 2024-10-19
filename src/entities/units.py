"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import esper
import pygame
import os
from enum import Enum, auto
from typing import Dict
from CONSTANTS import (
    MINIFOLKS_SCALE,
    SWORDSMAN_HP, SWORDSMAN_ATTACK_RANGE, SWORDSMAN_ATTACK_DAMAGE, SWORDSMAN_MOVEMENT_SPEED, SWORDSMAN_ANIMATION_DURATIONS,
    ARCHER_HP, ARCHER_ATTACK_RANGE, ARCHER_ATTACK_DAMAGE, ARCHER_MOVEMENT_SPEED, ARCHER_PROJECTILE_SPEED, ARCHER_ANIMATION_DURATIONS,
    MAGE_HP, MAGE_ATTACK_RANGE, MAGE_ATTACK_DAMAGE, MAGE_MOVEMENT_SPEED, MAGE_PROJECTILE_SPEED, MAGE_ANIMATION_DURATIONS,
    HORSEMAN_HP, HORSEMAN_ATTACK_RANGE, HORSEMAN_ATTACK_DAMAGE, HORSEMAN_MOVEMENT_SPEED, HORSEMAN_ANIMATION_DURATIONS,
    TINY_RPG_SCALE,
    WEREBEAR_HP, WEREBEAR_ATTACK_RANGE, WEREBEAR_ATTACK_DAMAGE, WEREBEAR_MOVEMENT_SPEED, WEREBEAR_ANIMATION_DURATIONS
)
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState
from components.attack import MeleeAttack, ProjectileAttack, ProjectileType
from components.movement import Movement
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection

class UnitType(Enum):
    """Enum representing different types of units."""
    SWORDSMAN = auto()
    ARCHER = auto()
    MAGE = auto()
    HORSEMAN = auto()
    WEREBEAR = auto()

# Dictionary to store sprite sheets
sprite_sheets: Dict[TeamType, Dict[UnitType, pygame.Surface]] = {
    TeamType.TEAM1: {},
    TeamType.TEAM2: {}
}

def load_sprite_sheets():
    """Load all sprite sheets."""
    # team_colors = {TeamType.TEAM1: "Blue", TeamType.TEAM2: "Red"}
    team_colors = {TeamType.TEAM1: "Blue", TeamType.TEAM2: "Blue"} # Using blue for both teams for now
    unit_filenames = {
        UnitType.SWORDSMAN: "MiniSwordMan.png", 
        UnitType.ARCHER: "MiniArcherMan.png", 
        UnitType.MAGE: "MiniMage.png",
        UnitType.HORSEMAN: "MiniHorseman.png",
        UnitType.WEREBEAR: "Werebear.png"
    }

    for team, color in team_colors.items():
        for unit_type, filename in unit_filenames.items():
            path = os.path.join("assets", color, filename)
            sprite_sheets[team][unit_type] = pygame.image.load(path).convert_alpha()

def create_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a swordsman entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, MeleeAttack(range=SWORDSMAN_ATTACK_RANGE, damage=SWORDSMAN_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=SWORDSMAN_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.SWORDSMAN],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 5},
        animation_durations=SWORDSMAN_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
        attack_activation_frame=2
    ))
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
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.ARCHER],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
        animation_durations=ARCHER_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
        attack_activation_frame=7
    ))
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
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.MAGE],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 9},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 7},
        animation_durations=MAGE_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
        attack_activation_frame=7
    ))
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
    esper.add_component(entity, MeleeAttack(range=HORSEMAN_ATTACK_RANGE, damage=HORSEMAN_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=HORSEMAN_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.HORSEMAN],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 8, AnimationType.WALKING: 6, AnimationType.ATTACKING: 7, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 4, AnimationType.DYING: 6},
        animation_durations=HORSEMAN_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
        attack_activation_frame=3
    ))
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
    esper.add_component(entity, MeleeAttack(range=WEREBEAR_ATTACK_RANGE, damage=WEREBEAR_ATTACK_DAMAGE))
    esper.add_component(entity, Movement(speed=WEREBEAR_MOVEMENT_SPEED))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.WEREBEAR],
        frame_width=100,
        frame_height=100,
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ATTACKING: 8, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 2, AnimationType.DYING: 6},
        animation_durations=WEREBEAR_ANIMATION_DURATIONS,
        sprite_center_offset=(0, 0),
        attack_activation_frame=5
    ))
    esper.add_component(entity, Health(current=WEREBEAR_HP, maximum=WEREBEAR_HP))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity
