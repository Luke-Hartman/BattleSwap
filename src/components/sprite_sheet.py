"""SpriteSheet component module for Battle Swap.

This module contains the SpriteSheet component, which represents the sprite sheet data and animation frames for an entity.
"""

from dataclasses import dataclass
import pygame
from typing import Dict
from components.animation import AnimationType

@dataclass
class SpriteSheet:
    """Represents the sprite sheet data and animation frames for an entity."""

    surface: pygame.Surface
    """The pygame Surface containing the sprite sheet."""

    frame_width: int
    """Width of a single frame in the sprite sheet, in pixels."""

    frame_height: int
    """Height of a single frame in the sprite sheet, in pixels."""

    scale: int
    """Scale factor for rendering sprites."""

    frames: Dict[AnimationType, int]
    """Dictionary mapping AnimationType to the number of frames for that animation."""

    rows: Dict[AnimationType, int]
    """Dictionary mapping AnimationType to the row in the sprite sheet for that animation."""

    animation_durations: Dict[AnimationType, float]
    """Dictionary mapping AnimationType to the duration of the full animation cycle, in seconds."""
