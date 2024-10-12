"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import esper
import pygame
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType

def create_swordsman(x: int, y: int, team: TeamType, sprite_sheet: pygame.Surface) -> int:
    """Create a swordsman entity with all necessary components.

    Args:
        x (int): The x-coordinate of the swordsman's position.
        y (int): The y-coordinate of the swordsman's position.
        team (TeamType): The team the swordsman belongs to.
        sprite_sheet (pygame.Surface): The sprite sheet for the swordsman.

    Returns:
        int: The entity ID of the created swordsman.
    """
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheet,
        frame_width=32,
        frame_height=32,
        scale=4,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 5},
        animation_durations={AnimationType.IDLE: 0.8, AnimationType.WALKING: 0.6, AnimationType.ATTACKING: 0.6, AnimationType.DYING: 0.8}
    ))
    return entity

def create_archer(x: int, y: int, team: TeamType, sprite_sheet: pygame.Surface) -> int:
    """Create an archer entity with all necessary components.

    Args:
        x (int): The x-coordinate of the archer's position.
        y (int): The y-coordinate of the archer's position.
        team (TeamType): The team the archer belongs to.
        sprite_sheet (pygame.Surface): The sprite sheet for the archer.

    Returns:
        int: The entity ID of the created archer.
    """
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheet,
        frame_width=32,
        frame_height=32,
        scale=4,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 11, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 6},
        animation_durations={AnimationType.IDLE: 0.8, AnimationType.WALKING: 0.6, AnimationType.ATTACKING: 1.1, AnimationType.DYING: 0.8}
    ))
    return entity
