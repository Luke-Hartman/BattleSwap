from pygame import Vector2
from typing import List, Optional
from dataclasses import dataclass

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

