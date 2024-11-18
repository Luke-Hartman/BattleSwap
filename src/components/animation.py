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

    ABILITY1 = auto()
    """The highest priority ability animation state."""

    ABILITY2 = auto()
    """The second highest priority ability animation state."""

    ABILITY3 = auto()
    """The third highest priority ability animation state."""

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

    time_elapsed: float = 0.0
    """The time elapsed since the animation began, in seconds."""
