"""UnitState component module for Battle Swap.

This module contains the UnitState component, which represents the current state of a unit.
"""

from dataclasses import dataclass
from enum import Enum, auto

class State(Enum):
    """Enum representing different states a unit can be in."""
    IDLE = auto()
    PURSUING = auto()
    ABILITY1 = auto()
    ABILITY2 = auto()
    ABILITY3 = auto()
    DEAD = auto()

@dataclass
class UnitState:
    """Represents the current state and target of a unit."""
    state: State = State.IDLE
