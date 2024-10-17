"""Orientation component module for Battle Swap.

This module contains the Orientation component, which represents the facing direction of an entity.
"""

from dataclasses import dataclass
from enum import Enum, auto

class FacingDirection(Enum):
    """Enum representing the facing direction of an entity."""
    LEFT = -1
    RIGHT = 1

@dataclass
class Orientation:
    """Represents the facing direction of an entity."""
    facing: FacingDirection
