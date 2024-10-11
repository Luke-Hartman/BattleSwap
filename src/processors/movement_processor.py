"""Movement processor for the Battle Swap game."""

import esper
import math
from components.position import Position
from components.velocity import Velocity
from components.team import Team, TeamType
from components.combat import Combat
from components.health import Health

class MovementProcessor(esper.Processor):
    """Processor responsible for updating entity positions."""

    def __init__(self, minx: int, maxx: int, miny: int, maxy: int):
        self.minx = minx
        self.maxx = maxx
        self.miny = miny
        self.maxy = maxy

    def process(self):
        """Update the position of all entities with a Position component."""
        entities = list(esper.get_components(Position, Velocity, Team, Combat, Health))
        
        for ent1, (pos1, vel1, team1, combat1, health1) in entities:
            if health1.current_health <= 0:
                continue

            closest_enemy = None
            closest_distance = float('inf')

            for ent2, (pos2, vel2, team2, combat2, health2) in entities:
                if ent1 != ent2 and team1.team_type != team2.team_type and health2.current_health > 0:
                    distance = math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)
                    if distance < closest_distance:
                        closest_enemy = pos2
                        closest_distance = distance

            if closest_enemy:
                if closest_distance > combat1.attack_range:
                    dx = closest_enemy.x - pos1.x
                    dy = closest_enemy.y - pos1.y
                    length = math.sqrt(dx**2 + dy**2)
                    vel1.dx = (dx / length) * 2  # Adjust speed as needed
                    vel1.dy = (dy / length) * 2
                else:
                    vel1.dx = 0
                    vel1.dy = 0

            pos1.x += vel1.dx
            pos1.y += vel1.dy

            # Wrap around screen
            pos1.x = pos1.x % self.maxx
            pos1.y = pos1.y % self.maxy