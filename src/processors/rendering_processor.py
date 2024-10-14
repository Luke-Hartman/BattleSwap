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
from processors.collision_processor import get_hitbox

class RenderingProcessor(esper.Processor):
    """
    Processor responsible for rendering entities.

    Attributes:
        screen (pygame.Surface): The game screen surface to render on.
    """

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the RenderingProcessor.

        Args:
            screen (pygame.Surface): The game screen surface to render on.
        """
        self.screen = screen

    def process(self, dt: float):
        """
        Process all entities with necessary components and render them.

        Args:
            dt (float): Delta time since last frame, in seconds.
        """
        self.screen.fill((34, 100, 34))
        for ent, (pos, anim_state, sprite_sheet, team) in esper.get_components(Position, AnimationState, SpriteSheet, Team):
            frame = self.get_frame(anim_state, sprite_sheet)
            
            if esper.has_component(ent, Orientation): # Currently only units have orientation
                orientation = esper.component_for_entity(ent, Orientation)
                if orientation.facing == FacingDirection.LEFT:
                    frame = pygame.transform.flip(frame, True, False)
            elif esper.has_component(ent, Velocity): # So this is only projectiles
                velocity = esper.component_for_entity(ent, Velocity)
                angle = math.atan2(velocity.y, velocity.x)
                frame = pygame.transform.rotate(frame, -math.degrees(angle))

            scaled_frame = pygame.transform.scale(frame, (sprite_sheet.frame_width * sprite_sheet.scale, sprite_sheet.frame_height * sprite_sheet.scale))
            
            # Calculate the position to center the sprite on the unit's position
            sprite_pos = (
                pos.x - sprite_sheet.scaled_sprite_size[0] // 2 + sprite_sheet.scaled_sprite_offset[0],
                pos.y - sprite_sheet.scaled_sprite_size[1] // 2 + sprite_sheet.scaled_sprite_offset[1]
            )
            self.screen.blit(scaled_frame, sprite_pos)
            
            # Draw hitbox
            hitbox = get_hitbox(sprite_sheet, pos)
            pygame.draw.rect(self.screen, (255, 0, 0), hitbox, 1)  # Red rectangle for hitbox

            # Draw circle at unit's position
            pygame.draw.circle(self.screen, (0, 255, 0), (pos.x, pos.y), 3)  # Green circle at unit's position

            # Draw health bar if entity has Health component and is not dead
            if esper.has_component(ent, Health) and esper.has_component(ent, UnitState):
                health = esper.component_for_entity(ent, Health)
                unit_state = esper.component_for_entity(ent, UnitState)
                if unit_state.state != State.DEAD:
                    self.draw_health_bar(pos, sprite_sheet, health, team)

        pygame.display.flip()

    def get_frame(self, anim_state: AnimationState, sprite_sheet: SpriteSheet) -> pygame.Surface:
        """
        Get the current frame of an animation from the sprite sheet.

        Args:
            anim_state (AnimationState): The AnimationState component containing the current frame information.
            sprite_sheet (SpriteSheet): The SpriteSheet component containing the sprite sheet data and animation frames.

        Returns:
            pygame.Surface: The current frame of the animation.
        """
        row = sprite_sheet.rows[anim_state.type]
        col = anim_state.current_frame
        frame = sprite_sheet.surface.subsurface((col * sprite_sheet.frame_width, row * sprite_sheet.frame_height, sprite_sheet.frame_width, sprite_sheet.frame_height))
        if frame.get_alpha() is None:
            frame = frame.convert_alpha()
        return frame

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
