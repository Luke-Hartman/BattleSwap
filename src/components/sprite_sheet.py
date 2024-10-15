"""SpriteSheet component module for Battle Swap.

This module contains the SpriteSheet component, which represents the sprite sheet data, animation frames, and sprite information for an entity.
"""

import pygame
from typing import Dict, Tuple
from components.animation import AnimationType

class SpriteSheet(pygame.sprite.Sprite):
    """Represents the sprite sheet data, animation frames, and sprite information for an entity."""

    def __init__(self, surface: pygame.Surface, frame_width: int, frame_height: int, scale: int,
                 frames: Dict[AnimationType, int], rows: Dict[AnimationType, int],
                 animation_durations: Dict[AnimationType, float], sprite_offset: Tuple[int, int],
                 sprite_size: Tuple[int, int], attack_activation_frame: int):
        super().__init__()
        self.surface = surface
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.scale = scale
        self.frames = frames
        self.rows = rows
        self.animation_durations = animation_durations
        self.sprite_offset = sprite_offset
        self.sprite_size = sprite_size
        self.attack_activation_frame = attack_activation_frame

        self.image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    @property
    def scaled_sprite_offset(self) -> Tuple[int, int]:
        """Returns the scaled sprite offset."""
        return (self.sprite_offset[0] * self.scale, self.sprite_offset[1] * self.scale)

    @property
    def scaled_sprite_size(self) -> Tuple[int, int]:
        """Returns the scaled sprite size."""
        return (self.sprite_size[0] * self.scale, self.sprite_size[1] * self.scale)

    def update_frame(self, animation_type: AnimationType, frame: int):
        """Update the sprite's image to the specified frame of the animation."""
        row = self.rows[animation_type]
        col = frame
        rect = pygame.Rect(col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height)
        self.image = self.surface.subsurface(rect).copy()
        if self.scale != 1:
            self.image = pygame.transform.scale(self.image, (self.frame_width * self.scale, self.frame_height * self.scale))
        self.rect = self.image.get_rect()
