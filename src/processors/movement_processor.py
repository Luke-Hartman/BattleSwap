"""Movement processor for the Battle Swap game."""

import esper
from components.position import Position
from components.velocity import Velocity

class MovementProcessor(esper.Processor):
    """Processor responsible for updating entity positions."""

    def __init__(self, minx: int, maxx: int, miny: int, maxy: int):
        """Initialize the MovementProcessor.

        Args:
            minx: The minimum x-coordinate.
            maxx: The maximum x-coordinate.
            miny: The minimum y-coordinate.
            maxy: The maximum y-coordinate.
        """
        super().__init__()
        self.minx = minx
        self.maxx = maxx
        self.miny = miny
        self.maxy = maxy

    def process(self):
        """Update the position of all entities with a Position component."""
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            pos.x += vel.dx
            pos.y += vel.dy

            # Wrap around screen
            pos.x = pos.x % self.maxx
            pos.y = pos.y % self.maxy