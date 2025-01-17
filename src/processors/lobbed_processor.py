import math
import esper
from pygame import Vector2
from components.position import Position
from game_constants import gc
from components.lobbed import Lobbed
from events import emit_event, LOBBED_ARRIVED, LobbedArrivedEvent

def calculate_position(lobbed: Lobbed) -> Vector2:
    # Calculate initial velocity needed to reach max_range
    # Using v = sqrt(g * R / sin(2θ)) where θ = 45° for max range
    initial_velocity = math.sqrt(gc.GRAVITY * lobbed.max_range / math.sin(math.pi/2))
    
    # Get the horizontal distance and direction
    displacement = lobbed.target - lobbed.start
    distance = displacement.length()
    if distance == 0:
        return lobbed.start
        
    # Calculate launch angle needed to hit target
    # θ = 1/2 * arcsin(g * d / v^2)
    launch_angle = 0.5 * math.asin(
        min(1.0, gc.GRAVITY * distance / (initial_velocity * initial_velocity))
    )
    
    # Decompose initial velocity into components
    direction = displacement.normalize()
    vx = initial_velocity * math.cos(launch_angle) * direction.x
    vy = initial_velocity * math.cos(launch_angle) * direction.y
    vz = initial_velocity * math.sin(launch_angle)
    
    # Calculate current position
    x = lobbed.start.x + vx * lobbed.time_passed
    y = lobbed.start.y + vy * lobbed.time_passed
    z = vz * lobbed.time_passed - 0.5 * gc.GRAVITY * lobbed.time_passed * lobbed.time_passed
    
    # If we've hit the ground or passed the target, return target position
    if z <= 0 or Vector2(x, y).distance_to(lobbed.start) >= distance:
        return lobbed.target
        
    # Project 3D position onto 2D plane by adding height to y-coordinate
    return Vector2(x, y - 2*z)  # Subtract z because pygame y increases downward

class LobbedProcessor:

    def process(self, dt: float):
        for entity, (position, lobbed) in esper.get_components(Position, Lobbed):
            lobbed.time_passed += dt
            new_position = calculate_position(lobbed)
            position.x = new_position.x
            position.y = new_position.y
            if new_position == lobbed.target:
                emit_event(LOBBED_ARRIVED, event=LobbedArrivedEvent(entity))
                esper.delete_entity(entity)
