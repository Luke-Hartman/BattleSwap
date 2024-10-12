"""
AnimationState component module for Battle Swap.

This module contains the AnimationState component and AnimationType enum, which represent
the animation state of an entity in the game.
"""

from dataclasses import dataclass
from enum import Enum, auto

class AnimationType(Enum):
    """
    Enum representing different types of animations available for entities.
    """

    IDLE = auto()
    """The idle animation state."""

    WALKING = auto()
    """The walking animation state."""

    ATTACKING = auto()
    """The attacking animation state."""

    DYING = auto()
    """The dying animation state."""

@dataclass
class AnimationState:
    """
    Represents the current animation state of an entity.
    """

    type: AnimationType
    """The current type of animation being played."""

    current_frame: int = 0
    """The index of the current frame in the animation sequence."""

    current_time: float = 0.0
    """The current time elapsed in the animation cycle, in seconds."""
