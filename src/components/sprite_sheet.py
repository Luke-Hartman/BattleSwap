"""SpriteSheet component module for Battle Swap.

This module contains the SpriteSheet component, which represents the sprite sheet data, animation frames, and sprite information for an entity.
"""

from dataclasses import dataclass
import pygame
from typing import Dict, Tuple
from components.animation import AnimationType

@dataclass
class SpriteSheet:
    """Represents the sprite sheet data, animation frames, and sprite information for an entity."""

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

    sprite_offset: Tuple[int, int]
    """The offset of the sprite from the top-left corner of the frame (x, y), in pixels."""

    sprite_size: Tuple[int, int]
    """The actual size of the sprite (width, height) within the frame, in pixels."""

    attack_activation_frame: int
    """The frame number when the attack is activated (e.g., sword swing)."""

    @property
    def scaled_sprite_offset(self) -> Tuple[int, int]:
        """Returns the scaled sprite offset."""
        return (self.sprite_offset[0] * self.scale, self.sprite_offset[1] * self.scale)

    @property
    def scaled_sprite_size(self) -> Tuple[int, int]:
        """Returns the scaled sprite size."""
        return (self.sprite_size[0] * self.scale, self.sprite_size[1] * self.scale)

    @property
    def scaled_hitbox(self) -> pygame.Rect:
        """Returns the scaled hitbox as a pygame.Rect, centered on the sprite."""
        return pygame.Rect(
            self.sprite_offset[0] * self.scale,
            self.sprite_offset[1] * self.scale,
            self.sprite_size[0] * self.scale,
            self.sprite_size[1] * self.scale
        )
