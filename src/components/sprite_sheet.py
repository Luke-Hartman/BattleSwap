"""SpriteSheet component module for Battle Swap.

This module contains the SpriteSheet component, which represents the sprite sheet data, animation frames, and sprite information for an entity.
"""

import pygame
from typing import Dict, Optional, Tuple
from components.animation import AnimationType

class SpriteSheet(pygame.sprite.Sprite):
    """Represents the sprite sheet data, animation frames, and sprite information for an entity."""

    def __init__(self,
        surface: pygame.Surface,
        frame_width: int,
        frame_height: int,
        scale: int,
        frames: Dict[AnimationType, int],
        rows: Dict[AnimationType, int],
        animation_durations: Dict[AnimationType, float],
        sprite_center_offset: Tuple[int, int],
        start_frames: Optional[Dict[AnimationType, int]] = None,
        synchronized_animations: Optional[Dict[AnimationType, bool]] = None,
        flip_frames: bool = False,
        layer: int = 0
    ):
        super().__init__()
        self.surface = surface
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.scale = scale
        self.frames = frames
        self.rows = rows
        self.animation_durations = animation_durations
        self._original_sprite_center_offset = sprite_center_offset
        self.sprite_center_offset = sprite_center_offset
        self.image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.start_frames = start_frames
        self.flip_frames = flip_frames
        self.layer = layer
        self._processed_frames = {}
        self.synchronized_animations = synchronized_animations if synchronized_animations is not None else {}
        
        # Store original frames to track which animations were provided
        self._original_frames = set(frames.keys())
        
        # Create default spawn animation if not provided and death animation exists
        if AnimationType.SPAWNING not in self.frames and AnimationType.DYING in self.frames:
            # Create a new row for the spawn animation by copying and reversing death frames
            self._create_spawn_animation_row()

    def _create_spawn_animation_row(self):
        """Create a new row in the sprite sheet for the spawn animation by copying and reversing death frames."""
        death_row = self.rows[AnimationType.DYING]
        death_frames = self.frames[AnimationType.DYING]
        
        # Find the next available row (after the highest existing row)
        spawn_row = self.surface.get_height() // self.frame_height
        
        # Create a new surface with an additional row
        new_height = self.surface.get_height() + self.frame_height
        new_surface = pygame.Surface((self.surface.get_width(), new_height), pygame.SRCALPHA)
        new_surface.blit(self.surface, (0, 0))
        
        # Copy death frames in reverse order to the new spawn row
        for i in range(death_frames):
            # Source: death frame i
            source_rect = pygame.Rect(
                i * self.frame_width,
                death_row * self.frame_height,
                self.frame_width,
                self.frame_height
            )
            source_frame = self.surface.subsurface(source_rect)
            
            # Destination: spawn frame (death_frames - 1 - i)
            dest_x = (death_frames - 1 - i) * self.frame_width
            dest_y = spawn_row * self.frame_height
            new_surface.blit(source_frame, (dest_x, dest_y))
        
        # Update the surface and animation data
        self.surface = new_surface
        self.frames[AnimationType.SPAWNING] = death_frames
        self.rows[AnimationType.SPAWNING] = spawn_row
        self.animation_durations[AnimationType.SPAWNING] = self.animation_durations[AnimationType.DYING]

    def update_frame(self, animation_type: AnimationType, frame: int):
        """Update the sprite's image to the specified frame of the animation."""
        if (animation_type, frame) in self._processed_frames:
            self.image, self.sprite_center_offset, self.rect = self._processed_frames[(animation_type, frame)]
            return
        row = self.rows[animation_type]
        if self.start_frames is not None:
            frame = self.start_frames.get(animation_type, 0) + frame
        
        col = frame
        rect = pygame.Rect(
            col * self.frame_width,
            row * self.frame_height,
            self.frame_width,
            self.frame_height
        )
        self.image = self.surface.subsurface(rect).copy()
        if self.scale != 1:
            self.image = pygame.transform.scale(self.image, (self.frame_width * self.scale, self.frame_height * self.scale))
        if self.flip_frames:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.sprite_center_offset = (
            self._original_sprite_center_offset[0] * self.scale,
            self._original_sprite_center_offset[1] * self.scale
        )
        self.rect.center = (
            self.rect.centerx + self.sprite_center_offset[0],
            self.rect.centery + self.sprite_center_offset[1]
        )
        self._processed_frames[(animation_type, frame)] = (self.image, self.sprite_center_offset, self.rect)