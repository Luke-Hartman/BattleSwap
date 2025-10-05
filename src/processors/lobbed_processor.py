import math
import esper
from pygame import Vector2
from components.position import Position
from components.static import StaticComponent
from game_constants import gc
from components.lobbed import Lobbed
from events import emit_event, LOBBED_ARRIVED, LobbedArrivedEvent

def calculate_position(lobbed: Lobbed) -> Vector2:    
    # Get the horizontal distance and direction
    displacement = lobbed.target - lobbed.start
    distance = displacement.length()
    if distance == 0:
        return lobbed.start
        
    # Calculate launch angle needed to hit target
    # θ = 1/2 * arcsin(g * d / v^2)
    launch_angle = 0.5 * math.asin(
        min(1.0, gc.GRAVITY * distance / (lobbed.initial_velocity * lobbed.initial_velocity))
    )
    
    # Decompose initial velocity into components
    direction = displacement.normalize()
    vx = lobbed.initial_velocity * math.cos(launch_angle) * direction.x
    vy = lobbed.initial_velocity * math.cos(launch_angle) * direction.y
    vz = lobbed.initial_velocity * math.sin(launch_angle)
    
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
            # Store previous position for distance calculation
            prev_x = position.x
            prev_y = position.y
            
            lobbed.time_passed += dt
            new_position = calculate_position(lobbed)
            
            # Calculate 3D distance moved for static buildup
            if esper.has_component(entity, StaticComponent):
                # Get the 3D position components
                displacement = lobbed.target - lobbed.start
                distance_2d = displacement.length()
                if distance_2d > 0:
                    # Calculate launch angle and velocity components
                    launch_angle = 0.5 * math.asin(
                        min(1.0, gc.GRAVITY * distance_2d / (lobbed.initial_velocity * lobbed.initial_velocity))
                    )
                    direction = displacement.normalize()
                    vx = lobbed.initial_velocity * math.cos(launch_angle) * direction.x
                    vy = lobbed.initial_velocity * math.cos(launch_angle) * direction.y
                    vz = lobbed.initial_velocity * math.sin(launch_angle)
                    
                    # Current 3D position
                    current_x = lobbed.start.x + vx * lobbed.time_passed
                    current_y = lobbed.start.y + vy * lobbed.time_passed
                    current_z = vz * lobbed.time_passed - 0.5 * gc.GRAVITY * lobbed.time_passed * lobbed.time_passed
                    
                    # Previous 3D position
                    prev_time = lobbed.time_passed - dt
                    prev_x_3d = lobbed.start.x + vx * prev_time
                    prev_y_3d = lobbed.start.y + vy * prev_time
                    prev_z_3d = vz * prev_time - 0.5 * gc.GRAVITY * prev_time * prev_time
                    
                    # Calculate 3D distance moved
                    dx = current_x - prev_x_3d
                    dy = current_y - prev_y_3d
                    dz = current_z - prev_z_3d
                    distance_3d = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    # Add to static charge
                    static_component = esper.component_for_entity(entity, StaticComponent)
                    static_component.static_charge += distance_3d * static_component.stacks
            
            position.x = new_position.x
            position.y = new_position.y
            if new_position == lobbed.target:
                emit_event(LOBBED_ARRIVED, event=LobbedArrivedEvent(entity))
                if lobbed.destroy_on_arrival:
                    esper.delete_entity(entity)
                else:
                    esper.remove_component(entity, Lobbed)
