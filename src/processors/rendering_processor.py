"""
Rendering processor module for Battle Swap.

This module contains the RenderingProcessor class, which is responsible for
rendering entities with Position, AnimationState, SpriteSheet, and Team components.
"""

import esper
import pygame
from components.aura import Aura
from components.hitbox import Hitbox
from components.position import Position
from components.range_indicator import RangeIndicator
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.health import Health
from components.unit_state import UnitState, State
from camera import Camera
from game_constants import gc

def draw_battlefield(screen: pygame.Surface, camera: Camera, include_no_mans_land: bool = False):
    """Draw the battlefield background."""
    battlefield_color = (34, 100, 34)
    battlefield_rect = pygame.Rect(
        -camera.x,
        -camera.y,
        gc.BATTLEFIELD_WIDTH,
        gc.BATTLEFIELD_HEIGHT
    )
    pygame.draw.rect(screen, battlefield_color, battlefield_rect)
    if include_no_mans_land:
        pygame.draw.line(screen, (15, 50, 15), 
                         (gc.BATTLEFIELD_WIDTH // 2 - gc.NO_MANS_LAND_WIDTH // 2 - camera.x, -camera.y), 
                         (gc.BATTLEFIELD_WIDTH // 2 - gc.NO_MANS_LAND_WIDTH // 2 - camera.x, gc.BATTLEFIELD_HEIGHT - camera.y), 
                         2)
        pygame.draw.line(screen, (15, 50, 15), 
                         (gc.BATTLEFIELD_WIDTH // 2 + gc.NO_MANS_LAND_WIDTH // 2 - camera.x, -camera.y), 
                         (gc.BATTLEFIELD_WIDTH // 2 + gc.NO_MANS_LAND_WIDTH // 2 - camera.x, gc.BATTLEFIELD_HEIGHT - camera.y), 
                         2)

class RenderingProcessor(esper.Processor):
    """
    Processor responsible for rendering entities.
    """

    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera
        self.battlefield_rect = pygame.Rect(0, 0, gc.BATTLEFIELD_WIDTH, gc.BATTLEFIELD_HEIGHT)

    def process(self, dt: float):
        # Draw all auras
        for ent, (aura, position) in esper.get_components(Aura, Position):
            # Draw filled circle with opacity
            surface = pygame.Surface((aura.radius * 2, aura.radius * 2), pygame.SRCALPHA)
            # Filling
            pygame.draw.circle(surface, (*aura.color, 25), (aura.radius, aura.radius), aura.radius)
            # Outline
            pygame.draw.circle(self.screen, (*aura.color, 120), (position.x - self.camera.x, position.y - self.camera.y), aura.radius, 1)
            self.screen.blit(surface, (position.x - self.camera.x - aura.radius, position.y - self.camera.y - aura.radius))

        # Draw range indicators
        for ent, (range_indicator, position) in esper.get_components(RangeIndicator, Position):
            if range_indicator.enabled:
                # Draw filled circle with opacity
                surface = pygame.Surface((range_indicator.range * 2, range_indicator.range * 2), pygame.SRCALPHA)
                pygame.draw.circle(surface, (200, 200, 200, 120), (range_indicator.range, range_indicator.range), range_indicator.range, 1)
                self.screen.blit(surface, (position.x - self.camera.x - range_indicator.range, position.y - self.camera.y - range_indicator.range))

        # Get all entities with necessary components
        entities = esper.get_components(Position, SpriteSheet)
        
        # Sort entities based on their y-coordinate (higher y-value means lower on screen)
        sorted_entities = sorted(entities, key=lambda e: (e[1][1].layer, e[1][0].y))
        
        for ent, (pos, sprite_sheet) in sorted_entities:
            render_pos = sprite_sheet.rect.move(-self.camera.x, -self.camera.y)
            self.screen.blit(sprite_sheet.image, render_pos)

            # if esper.has_component(ent, Hitbox):
            #     hitbox = esper.component_for_entity(ent, Hitbox)
            #     pygame.draw.rect(
            #         self.screen,
            #         (255, 0, 0),
            #         (pos.x - self.camera.x - hitbox.width / 2, pos.y - self.camera.y - hitbox.height / 2, hitbox.width, hitbox.height),
            #         1
            #     )

            # Draw health bar if entity has Health, Team, and UnitState components, is not dead, and health is not full
            if (
                esper.has_component(ent, Health) and
                esper.has_component(ent, Team) and
                esper.has_component(ent, UnitState)
            ):
                health = esper.component_for_entity(ent, Health)
                team = esper.component_for_entity(ent, Team)
                unit_state = esper.component_for_entity(ent, UnitState)
                hitbox = esper.component_for_entity(ent, Hitbox)
                if unit_state.state != State.DEAD and health.current < health.maximum:
                    self.draw_health_bar(pos, health, team, hitbox)

    def draw_health_bar(self, pos: Position, health: Health, team: Team, hitbox: Hitbox):
        """Draw a health bar above the entity."""
        bar_width = 20
        bar_height = 5  # pixels
        bar_y_offset = 8  # pixels above the unit's hitbox

        # Position the health bar above the hitbox
        bar_x = pos.x - bar_width // 2
        bar_y = pos.y - hitbox.height/2 - bar_height - bar_y_offset

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
