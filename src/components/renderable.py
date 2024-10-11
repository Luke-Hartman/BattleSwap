"""Renderable component for the Battle Swap game."""

from dataclasses import dataclass, field
import pygame

@dataclass
class Renderable:
    """Represents the visual properties of an entity."""

    sprite_sheet: pygame.Surface
    """The sprite sheet containing all animation frames."""

    frame_width: int
    """The width of a single frame in pixels."""

    frame_height: int
    """The height of a single frame in pixels."""

    scale: int = 1
    """The scale factor for rendering the sprite."""

    current_frame: int = 0
    """The index of the current frame being displayed."""

    animation_frames: dict[int, list[pygame.Surface]] = field(init=False)
    """A dictionary containing all animation frames organized by row."""

    def __post_init__(self):
        self.animation_frames = self.load_animation_frames()

    def load_animation_frames(self) -> dict[int, list[pygame.Surface]]:
        """Load and scale all animation frames from the sprite sheet."""
        frames = {}
        sheet_width = self.sprite_sheet.get_width()
        sheet_height = self.sprite_sheet.get_height()
        
        for row in range(sheet_height // self.frame_height):
            frames[row] = []
            for col in range(sheet_width // self.frame_width):
                frame = self.sprite_sheet.subsurface((col * self.frame_width, row * self.frame_height, self.frame_width, self.frame_height))
                frame = pygame.transform.scale(frame, (self.frame_width * self.scale, self.frame_height * self.scale))
                frames[row].append(frame)
        
        return frames