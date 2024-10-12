"""
Rendering processor module for Battle Swap.

This module contains the RenderingProcessor class, which is responsible for
rendering entities with Position, AnimationState, and SpriteSheet components.
"""

import esper
import pygame
from components.position import Position
from components.animation import AnimationState
from components.sprite_sheet import SpriteSheet

class RenderingProcessor(esper.Processor):
    """
    Processor responsible for rendering entities.

    Attributes:
        screen (pygame.Surface): The game screen surface to render on.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the RenderingProcessor.

        Args:
            screen (pygame.Surface): The game screen surface to render on.
        """
        self.screen = screen

    def process(self, dt: float):
        """
        Process all entities with necessary components and render them.

        Args:
            dt (float): Delta time since last frame, in seconds.
        """
        self.screen.fill((34, 100, 34))  # Fill with forest green color
        for ent, (pos, anim_state, sprite_sheet) in esper.get_components(Position, AnimationState, SpriteSheet):
            frame = self.get_frame(anim_state, sprite_sheet)
            scaled_frame = pygame.transform.scale(frame, (sprite_sheet.frame_width * sprite_sheet.scale, sprite_sheet.frame_height * sprite_sheet.scale))
            dest_rect = scaled_frame.get_rect(center=(pos.x, pos.y))
            self.screen.blit(scaled_frame, dest_rect)
        pygame.display.flip()

    def get_frame(self, anim_state: AnimationState, sprite_sheet: SpriteSheet) -> pygame.Surface:
        """
        Get the current frame of an animation from the sprite sheet.

        Args:
            anim_state (AnimationState): The AnimationState component containing the current frame information.
            sprite_sheet (SpriteSheet): The SpriteSheet component containing the sprite sheet data and animation frames.

        Returns:
            pygame.Surface: The current frame of the animation.
        """
        row = sprite_sheet.rows[anim_state.type]
        col = anim_state.current_frame
        frame = sprite_sheet.surface.subsurface((col * sprite_sheet.frame_width, row * sprite_sheet.frame_height, sprite_sheet.frame_width, sprite_sheet.frame_height))
        if frame.get_alpha() is None:
            frame = frame.convert_alpha()
        return frame
