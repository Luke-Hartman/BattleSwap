from pygame import Vector2
from typing import List, Optional
from dataclasses import dataclass
import math
from game_constants import gc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect

@dataclass
class Lobbed:
    """Component for entities that follow a ballistic trajectory.
    
    The trajectory is calculated in 3D but projected onto a 2D plane, where the
    z-coordinate (height) is added to the y-coordinate for display purposes.
    """
    
    start: Vector2
    target: Vector2
    max_range: float
    max_angle: float
    effects: List["Effect"]
    owner: Optional[int]
    destroy_on_arrival: bool
    time_passed: float = 0.0

    def __post_init__(self):
        displacement = self.target - self.start
        self.max_range = max(self.max_range, displacement.length())
        self.initial_velocity = self.calculate_velocity()

    def calculate_velocity(self) -> float:
        # Calculate initial velocity needed to reach max_range
        # Using v = sqrt(g * R / sin(2θ)) where θ = lobbed.max_angle
        return math.sqrt(gc.GRAVITY * self.max_range / math.sin(2 * self.max_angle))
