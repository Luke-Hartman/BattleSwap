"""UnitState component module for Battle Swap.

This module contains the UnitState component, which represents the current state and target of a unit.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

class State(Enum):
    """Enum representing different states a unit can be in."""
    IDLE = auto()
    PURSUING = auto()
    ATTACKING = auto()
    DEAD = auto()

@dataclass
class UnitState:
    """Represents the current state and target of a unit."""
    state: State = State.IDLE
    target: Optional[int] = None
