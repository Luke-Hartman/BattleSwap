"""
Rendering processor module for Battle Swap.

This module contains the RenderingProcessor class, which is responsible for
rendering entities with Position, AnimationState, SpriteSheet, and Team components.
"""

import esper
import pygame
import math
from components.position import Position
from components.animation import AnimationState
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.health import Health
from components.unit_state import UnitState, State
from components.orientation import Orientation, FacingDirection
from components.velocity import Velocity

class RenderingProcessor(esper.Processor):
    """
    Processor responsible for rendering entities.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def process(self, dt: float):
        self.screen.fill((34, 100, 34))
        
        # Get all entities with necessary components
        entities = esper.get_components(Position, AnimationState, SpriteSheet, Team)
        
        # Sort entities based on their y-coordinate (higher y-value means lower on screen)
        sorted_entities = sorted(entities, key=lambda e: e[1][0].y)
        
        for ent, (pos, anim_state, sprite_sheet, team) in sorted_entities:
            sprite_sheet.update_frame(anim_state.type, anim_state.current_frame)
            
            if esper.has_component(ent, Orientation):
                orientation = esper.component_for_entity(ent, Orientation)
                if orientation.facing == FacingDirection.LEFT:
                    sprite_sheet.image = pygame.transform.flip(sprite_sheet.image, True, False)
            elif esper.has_component(ent, Velocity):
                velocity = esper.component_for_entity(ent, Velocity)
                angle = math.atan2(velocity.y, velocity.x)
                sprite_sheet.image = pygame.transform.rotate(sprite_sheet.image, -math.degrees(angle))

            # Calculate the position to center the sprite on the unit's position
            sprite_pos = (
                pos.x - sprite_sheet.scaled_sprite_size[0] // 2 + sprite_sheet.scaled_sprite_offset[0],
                pos.y - sprite_sheet.scaled_sprite_size[1] // 2 + sprite_sheet.scaled_sprite_offset[1]
            )
            sprite_sheet.rect.topleft = sprite_pos
            self.screen.blit(sprite_sheet.image, sprite_sheet.rect)
            
            # # Draw hitbox
            # hitbox = pygame.Rect(
            #     pos.x - sprite_sheet.scaled_sprite_size[0] // 2,
            #     pos.y - sprite_sheet.scaled_sprite_size[1] // 2,
            #     sprite_sheet.scaled_sprite_size[0],
            #     sprite_sheet.scaled_sprite_size[1]
            # )
            # pygame.draw.rect(self.screen, (255, 0, 0), hitbox, 1)  # Red rectangle for hitbox

            # # Draw circle at unit's position
            # pygame.draw.circle(self.screen, (0, 255, 0), (pos.x, pos.y), 3)  # Green circle at unit's position

            # Draw health bar if entity has Health component, is not dead, and health is not full
            if esper.has_component(ent, Health) and esper.has_component(ent, UnitState):
                health = esper.component_for_entity(ent, Health)
                unit_state = esper.component_for_entity(ent, UnitState)
                if unit_state.state != State.DEAD and health.current < health.maximum:
                    self.draw_health_bar(pos, sprite_sheet, health, team)

        pygame.display.flip()

    def draw_health_bar(self, pos: Position, sprite_sheet: SpriteSheet, health: Health, team: Team):
        """Draw a health bar above the entity."""
        bar_width = sprite_sheet.scaled_sprite_size[0]
        bar_height = 5  # pixels
        bar_y_offset = 5  # pixels above the hitbox

        # Position the health bar above the hitbox
        bar_x = pos.x - bar_width // 2
        bar_y = pos.y - sprite_sheet.scaled_sprite_size[1] // 2 - bar_height - bar_y_offset

        # Draw the background (empty health bar)
        pygame.draw.rect(self.screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height))

        # Draw the filled portion of the health bar
        fill_width = int(bar_width * health.current / health.maximum)
        fill_color = (0, 255, 0) if team.type == TeamType.TEAM1 else (255, 0, 0)
        pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height))

        # Draw the border of the health bar
        pygame.draw.rect(self.screen, (192, 192, 192), (bar_x, bar_y, bar_width, bar_height), 1)
