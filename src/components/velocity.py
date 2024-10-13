"""Velocity component module for Battle Swap.

This module contains the Velocity component, which represents the current velocity of an entity.
"""

from dataclasses import dataclass

@dataclass
class Velocity:
    """Represents the current velocity of an entity."""

    x: float
    """The x-component of the velocity, in pixels per second."""

    y: float
    """The y-component of the velocity, in pixels per second."""
