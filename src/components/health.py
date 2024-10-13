"""Health component module for Battle Swap.

This module contains the Health component, which represents the current and maximum health of an entity.
"""

from dataclasses import dataclass

@dataclass
class Health:
    """Represents the current and maximum health of an entity."""

    current: int
    """The current health of the entity."""

    maximum: int
    """The maximum health of the entity."""
