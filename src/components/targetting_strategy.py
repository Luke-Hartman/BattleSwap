"""Targetting strategy component for Battle Swap."""

from dataclasses import dataclass
from enum import Enum, auto

class TargettingStrategyType(Enum):
    """The type of targetting strategy."""

    NEAREST_ENEMY = auto()
    STRONGEST_ALLY = auto()

@dataclass
class TargettingStrategyComponent:
    """Represents a targetting strategy."""

    type: TargettingStrategyType
    """The type of targetting strategy."""
