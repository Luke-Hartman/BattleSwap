"""Angle component module for Battle Swap."""

from dataclasses import dataclass
import math

@dataclass
class Angle:
    """Component for storing an angle."""
    angle: float

    @property
    def x(self) -> float:
        """Return the x component of the angle."""
        return math.cos(self.angle)

    @property
    def y(self) -> float:
        """Return the y component of the angle."""
        return math.sin(self.angle)
