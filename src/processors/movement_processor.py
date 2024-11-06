"""Movement processor module for Battle Swap.

This module contains the MovementProcessor class, which is responsible for
moving entities based on their velocity.
"""

import esper
from components.position import Position
from components.velocity import Velocity

class MovementProcessor(esper.Processor):
    """Processor responsible for moving entities."""

    def process(self, dt: float):
        for ent, (pos, velocity) in esper.get_components(Position, Velocity):
            pos.x += velocity.x * dt
            pos.y += velocity.y * dt