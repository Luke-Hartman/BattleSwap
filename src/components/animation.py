"""Animation component for the Battle Swap game."""

from dataclasses import dataclass

@dataclass
class Animation:
    """Represents the animation state of an entity."""

    row: int
    """The row in the sprite sheet for the current animation."""

    frame_count: int
    """The total number of frames in the animation."""

    frame_duration: int
    """The number of game ticks each frame should be displayed."""

    current_frame: int = 0
    """The index of the current frame in the animation."""

    frame_timer: int = 0
    """A timer to keep track of when to switch to the next frame."""