"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import esper
import pygame
import os
from enum import Enum, auto
from typing import Dict
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState
from components.attack import MeleeAttack, ProjectileAttack
from components.movement import Movement
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection

class UnitType(Enum):
    """Enum representing different types of units."""
    SWORDSMAN = auto()
    ARCHER = auto()

# Dictionary to store sprite sheets
sprite_sheets: Dict[TeamType, Dict[UnitType, pygame.Surface]] = {
    TeamType.TEAM1: {},
    TeamType.TEAM2: {}
}

def load_sprite_sheets():
    """Load all sprite sheets."""
    team_colors = {TeamType.TEAM1: "Blue", TeamType.TEAM2: "Red"}
    unit_filenames = {UnitType.SWORDSMAN: "MiniSwordMan.png", UnitType.ARCHER: "MiniArcherMan.png"}

    for team, color in team_colors.items():
        for unit_type, filename in unit_filenames.items():
            path = os.path.join("assets", color, filename)
            sprite_sheets[team][unit_type] = pygame.image.load(path).convert_alpha()

def create_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a swordsman entity with all necessary components.

    Args:
        x (int): The x-coordinate of the swordsman's position.
        y (int): The y-coordinate of the swordsman's position.
        team (TeamType): The team the swordsman belongs to.

    Returns:
        int: The entity ID of the created swordsman.
    """
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, MeleeAttack(range=25.0, damage=20))
    esper.add_component(entity, Movement(speed=50.0))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.SWORDSMAN],
        frame_width=32,
        frame_height=32,
        scale=2,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 5},
        animation_durations={AnimationType.IDLE: 0.8, AnimationType.WALKING: 0.6, AnimationType.ATTACKING: 1, AnimationType.DYING: 0.8},
        sprite_offset=(-13, -19),
        sprite_size=(7, 11),
        attack_activation_frame=2
    ))
    esper.add_component(entity, Health(current=100, maximum=100))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity

def create_archer(x: int, y: int, team: TeamType) -> int:
    """Create an archer entity with all necessary components.

    Args:
        x (int): The x-coordinate of the archer's position.
        y (int): The y-coordinate of the archer's position.
        team (TeamType): The team the archer belongs to.

    Returns:
        int: The entity ID of the created archer.
    """
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, ProjectileAttack(range=200.0, damage=15, projectile_speed=150.0))
    esper.add_component(entity, Movement(speed=40.0))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[team][UnitType.ARCHER],
        frame_width=32,
        frame_height=32,
        scale=2,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
        animation_durations={AnimationType.IDLE: 0.8, AnimationType.WALKING: 0.6, AnimationType.ATTACKING: 1.8, AnimationType.DYING: 1.2},
        sprite_offset=(-13, -19),
        sprite_size=(7, 11),
        attack_activation_frame=7
    ))
    esper.add_component(entity, Health(current=60, maximum=60))
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    return entity
