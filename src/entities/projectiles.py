"""Projectile creation module for Battle Swap.

This module contains functions for creating different types of projectiles with their corresponding components.
"""

import esper
import pygame
import os
from components.position import Position
from components.velocity import Velocity
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.projectile_damage import ProjectileDamage
from components.animation import AnimationState, AnimationType

# Dictionary to store projectile sprite sheets
projectile_sheets: dict[TeamType, pygame.Surface] = {}

def load_projectile_sheets():
    """Load all projectile sprite sheets."""
    team_colors = {TeamType.TEAM1: "Blue", TeamType.TEAM2: "Red"}
    
    for team, color in team_colors.items():
        path = os.path.join("assets", color, "HumansProjectiles.png")
        projectile_sheets[team] = pygame.image.load(path).convert_alpha()

def create_arrow(x: int, y: int, velocity_x: float, velocity_y: float, team: TeamType, damage: int) -> int:
    """Create an arrow entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, Velocity(x=velocity_x, y=velocity_y))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, SpriteSheet(
        surface=projectile_sheets[team],
        frame_width=16,
        frame_height=16,
        scale=4,
        frames={AnimationType.IDLE: 1},  # Only one frame for arrows
        rows={AnimationType.IDLE: 0},
        animation_durations={AnimationType.IDLE: 1.0},  # Duration doesn't matter for single frame
        sprite_offset=(0, 0),
        sprite_size=(16, 16),
        attack_activation_frame=0
    ))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, ProjectileDamage(damage=damage))
    return entity
