"""Movement processor module for Battle Swap.

This module contains the MovementProcessor class, which is responsible for
moving entities based on their velocity.
"""

import math
import esper
from components.angle import Angle
from components.angular_velocity import AngularVelocity
from components.forced_movement import ForcedMovement
from components.position import Position
from components.velocity import Velocity
from components.status_effect import StatusEffects, Immobilized

class VelocityProcessor(esper.Processor):
    """Processor responsible for translating entities."""

    def process(self, dt: float):
        for ent, (pos, velocity) in esper.get_components(Position, Velocity):
            # Check if entity is immobilized by status effect
            is_immobilized = False
            if esper.has_component(ent, StatusEffects):
                status_effects = esper.component_for_entity(ent, StatusEffects)
                is_immobilized = any(isinstance(effect, Immobilized) for effect in status_effects.active_effects())
            
            if not is_immobilized and not esper.has_component(ent, ForcedMovement):
                pos.x += velocity.x * dt
                pos.y += velocity.y * dt
        
        for ent, (angle, angular_velocity) in esper.get_components(Angle, AngularVelocity):
            # Check if entity is immobilized by status effect
            is_immobilized = False
            if esper.has_component(ent, StatusEffects):
                status_effects = esper.component_for_entity(ent, StatusEffects)
                is_immobilized = any(isinstance(effect, Immobilized) for effect in status_effects.active_effects())
            
            if not is_immobilized:
                angle.angle += angular_velocity.velocity * dt

        for ent, (pos, forced_movement) in esper.get_components(Position, ForcedMovement):
            dx = forced_movement.destination_x - pos.x
            dy = forced_movement.destination_y - pos.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance == 0:
                continue
            if distance < forced_movement.speed * dt:
                pos.x = forced_movement.destination_x
                pos.y = forced_movement.destination_y
                esper.remove_component(ent, ForcedMovement)
            else:
                pos.x += forced_movement.speed * dt * dx / distance
                pos.y += forced_movement.speed * dt * dy / distance
