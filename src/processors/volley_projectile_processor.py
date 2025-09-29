"""VolleyProjectile processor module for Battle Swap.

This module contains the VolleyProjectileProcessor class, which is responsible for
moving volley projectiles and applying their effects when they reach their target.
"""

import math
import esper
from components.position import Position
from components.volley_projectile import VolleyProjectile
from components.team import Team
from effects import Effect, Recipient

class VolleyProjectileProcessor(esper.Processor):
    """Processor responsible for moving volley projectiles and applying their effects."""
    
    def process(self, dt: float) -> None:
        """Process all volley projectiles."""
        for ent, (pos, volley) in esper.get_components(Position, VolleyProjectile):
            # Calculate direction to target
            dx = volley.target_x - pos.x
            dy = volley.target_y - pos.y
            distance_to_target = math.sqrt(dx**2 + dy**2)
            
            # Check if we've reached the target
            if distance_to_target <= volley.speed * dt:
                # We've reached the target, apply effects
                pos.x = volley.target_x
                pos.y = volley.target_y
                
                # Apply all effects
                for effect in volley.effects:
                    effect.apply(
                        owner=volley.owner,
                        parent=ent,
                        target=None
                    )
                
                # Remove the volley projectile
                esper.delete_entity(ent)
            elif distance_to_target > 0:
                velocity_x = dx/distance_to_target * volley.speed
                velocity_y = dy/distance_to_target * volley.speed
                
                pos.x += velocity_x * dt
                pos.y += velocity_y * dt
