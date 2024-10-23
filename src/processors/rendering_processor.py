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
from camera import Camera
from CONSTANTS import BATTLEFIELD_WIDTH, BATTLEFIELD_HEIGHT, NO_MANS_LAND_WIDTH

def draw_battlefield(screen: pygame.Surface, camera: Camera, include_no_mans_land: bool = False):
    """Draw the battlefield background."""
    battlefield_color = (34, 100, 34)
    battlefield_rect = pygame.Rect(
        -camera.x,
        -camera.y,
        BATTLEFIELD_WIDTH,
        BATTLEFIELD_HEIGHT
    )
    pygame.draw.rect(screen, battlefield_color, battlefield_rect)
    if include_no_mans_land:
        pygame.draw.line(screen, (15, 50, 15), 
                         (BATTLEFIELD_WIDTH // 2 - NO_MANS_LAND_WIDTH // 2 - camera.x, -camera.y), 
                         (BATTLEFIELD_WIDTH // 2 - NO_MANS_LAND_WIDTH // 2 - camera.x, BATTLEFIELD_HEIGHT - camera.y), 
                         2)
        pygame.draw.line(screen, (15, 50, 15), 
                         (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2 - camera.x, -camera.y), 
                         (BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH // 2 - camera.x, BATTLEFIELD_HEIGHT - camera.y), 
                         2)

class RenderingProcessor(esper.Processor):
    """
    Processor responsible for rendering entities.
    """

    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera
        self.battlefield_rect = pygame.Rect(0, 0, BATTLEFIELD_WIDTH, BATTLEFIELD_HEIGHT)

    def process(self, dt: float):        
        # Get all entities with necessary components
        entities = esper.get_components(Position, AnimationState, SpriteSheet, Team)
        
        # Sort entities based on their y-coordinate (higher y-value means lower on screen)
        sorted_entities = sorted(entities, key=lambda e: e[1][0].y)
        
        for ent, (pos, anim_state, sprite_sheet, team) in sorted_entities:
            sprite_sheet.update_frame(anim_state.type, anim_state.current_frame)
            x_offset = sprite_sheet.sprite_center_offset[0] * sprite_sheet.scale
            y_offset = sprite_sheet.sprite_center_offset[1] * sprite_sheet.scale
            
            if esper.has_component(ent, Orientation):
                orientation = esper.component_for_entity(ent, Orientation)
                if orientation.facing == FacingDirection.LEFT:
                    sprite_sheet.image = pygame.transform.flip(sprite_sheet.image, True, False)
            elif esper.has_component(ent, Velocity):
                velocity = esper.component_for_entity(ent, Velocity)
                angle = math.atan2(velocity.y, velocity.x)
                # See https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
                rotated_image = pygame.transform.rotate(sprite_sheet.image, -math.degrees(angle))
                new_rect = rotated_image.get_rect()
                x_offset = x_offset * math.cos(angle) - y_offset * math.sin(angle)
                y_offset = x_offset * math.sin(angle) + y_offset * math.cos(angle)
                sprite_sheet.image = rotated_image
                sprite_sheet.rect = new_rect

            # Calculate the position to center the sprite on the unit's position
            sprite_sheet.rect.center = (
                pos.x + x_offset,
                pos.y + y_offset
            )
            render_pos = sprite_sheet.rect.move(-self.camera.x, -self.camera.y)
            self.screen.blit(sprite_sheet.image, render_pos)

            # Draw health bar if entity has Health component, is not dead, and health is not full
            if esper.has_component(ent, Health) and esper.has_component(ent, UnitState):
                health = esper.component_for_entity(ent, Health)
                unit_state = esper.component_for_entity(ent, UnitState)
                if unit_state.state != State.DEAD and health.current < health.maximum:
                    self.draw_health_bar(pos, sprite_sheet, health, team)

    def draw_health_bar(self, pos: Position, sprite_sheet: SpriteSheet, health: Health, team: Team):
        """Draw a health bar above the entity."""
        bar_width = 20
        bar_height = 5  # pixels
        bar_y_offset = 16  # pixels above the unit's center

        # Position the health bar above the hitbox
        bar_x = pos.x - bar_width // 2
        bar_y = pos.y - bar_height - bar_y_offset

        # Apply camera offset to health bar position
        bar_pos = pygame.Rect(bar_x - self.camera.x, bar_y - self.camera.y, bar_width, bar_height)

        # Draw the background (empty health bar)
        pygame.draw.rect(self.screen, (64, 64, 64), bar_pos)

        # Draw the filled portion of the health bar
        fill_width = int(bar_width * health.current / health.maximum)
        fill_color = (0, 255, 0) if team.type == TeamType.TEAM1 else (255, 0, 0)
        pygame.draw.rect(self.screen, fill_color, (bar_pos.x, bar_pos.y, fill_width, bar_height))

        # Draw the border of the health bar
        pygame.draw.rect(self.screen, (192, 192, 192), bar_pos, 1)
