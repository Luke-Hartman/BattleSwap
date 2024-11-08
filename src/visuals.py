"""Enums for specifying different kinds of simple visuals.

For example, any visual which is simply a looping animation should be defined here.
"""

import os
from typing import Optional
import pygame
from enum import Enum, auto

from CONSTANTS import GAME_SPEED, MINIFOLKS_SCALE, TINY_RPG_SCALE
from components.animation import AnimationType
from components.sprite_sheet import SpriteSheet

class Visual(Enum):
    Arrow = auto()
    Fireball = auto()
    Explosion = auto()
    Healing = auto()
    CrusaderRedKnightFireSlash = auto()

visual_sheets: dict[Visual, pygame.Surface] = {}

def load_visual_sheets():
    """Load all visual sprite sheets."""
    visual_paths = {
        Visual.Arrow: os.path.join("assets", "effects", "HumansProjectiles.png"),
        Visual.Fireball: os.path.join("assets", "effects", "Wizard.png"),
        Visual.Explosion: os.path.join("assets", "effects", "explosiontip1_32x32.png"),
        Visual.Healing: os.path.join("assets", "units", "CrusaderCleric.png"),
        Visual.CrusaderRedKnightFireSlash: os.path.join("assets", "effects", "Knight-Attack03_Effect.png"),
    }
    for visual, path in visual_paths.items():
        visual_sheets[visual] = pygame.image.load(path).convert_alpha()

def create_visual_spritesheet(visual: Visual, duration: Optional[float] = None, scale: Optional[float] = None) -> SpriteSheet:
    """Get the sprite sheet for a visual."""
    if visual == Visual.Arrow:
        if duration is None:
            duration = 1.0 # Doesn't matter for single frame
        if scale is None:
            scale = MINIFOLKS_SCALE
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=16,
            frame_height=16,
            scale=scale,
            frames={AnimationType.IDLE: 1},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(-.5, -.5),
        )
    elif visual == Visual.Fireball:
        if duration is None:
            duration = 0.2 / GAME_SPEED
        if scale is None:
            scale = TINY_RPG_SCALE
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: 4},
            rows={AnimationType.IDLE: 5},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(-5, -2),
        )
    elif visual == Visual.Healing:
        if duration is None:
            duration = 1.0 / GAME_SPEED
        if scale is None:
            scale = TINY_RPG_SCALE
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: 4},
            rows={AnimationType.IDLE: 5},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
        )
    elif visual == Visual.Explosion:
        if duration is None:
            duration = 0.2 / GAME_SPEED
        if scale is None:
            scale = TINY_RPG_SCALE
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=32,
            frame_height=32,
            scale=scale,
            frames={AnimationType.IDLE: 6},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
        )
    elif visual == Visual.CrusaderRedKnightFireSlash:
        if duration is None:
            duration = 0.2 / GAME_SPEED
        if scale is None:
            scale = TINY_RPG_SCALE
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: 3},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
        )

