"""UnitState component module for Battle Swap.

This module contains the UnitState component, which represents the current state of a unit.
"""

from dataclasses import dataclass
from enum import Enum, auto

class State(Enum):
    """The state of a unit."""

    IDLE = auto()
    """The unit is idle."""
    ABILITY1 = auto()
    """The unit is using ability 1."""
    ABILITY2 = auto()
    """The unit is using ability 2."""
    ABILITY3 = auto()
    """The unit is using ability 3."""
    ABILITY4 = auto()
    """The unit is using ability 4."""
    ABILITY5 = auto()
    """The unit is using ability 5."""
    PURSUING = auto()
    """The unit is pursuing a target."""
    FLEEING = auto()
    """The unit is fleeing."""
    GRABBED = auto()
    """The unit is being grabbed by another unit."""
    GRABBING = auto()
    """The unit is grabbing another unit."""
    DEAD = auto()
    """The unit is dead."""

@dataclass
class UnitState:
    """Represents the current state of a unit."""
    state: State = State.IDLE
