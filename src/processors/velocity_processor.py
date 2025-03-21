"""Movement processor module for Battle Swap.

This module contains the MovementProcessor class, which is responsible for
moving entities based on their velocity.
"""

import esper
from components.angle import Angle
from components.angular_velocity import AngularVelocity
from components.immobile import Immobile
from components.position import Position
from components.velocity import Velocity

class VelocityProcessor(esper.Processor):
    """Processor responsible for translating entities."""

    def process(self, dt: float):
        for ent, (pos, velocity) in esper.get_components(Position, Velocity):
            if not esper.has_component(ent, Immobile):
                pos.x += velocity.x * dt
                pos.y += velocity.y * dt
        
        for ent, (angle, angular_velocity) in esper.get_components(Angle, AngularVelocity):
            if not esper.has_component(ent, Immobile):
                angle.angle += angular_velocity.velocity * dt
