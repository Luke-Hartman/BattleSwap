"""
Rendering processor module for Battle Swap.

This module contains the RenderingProcessor class, which is responsible for
rendering entities with Position, AnimationState, SpriteSheet, and Team components.
"""

import math
import esper
import pygame
from typing import Optional, Tuple
import pygame.gfxdraw
import pygame_gui
from components.animation import AnimationType
from components.aura import Aura
from components.can_have_item import CanHaveItem
from components.item import ItemComponent
from components.destination import Destination
from components.focus import Focus
from components.hitbox import Hitbox
from components.position import Position
from components.range_indicator import RangeIndicator
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.health import Health
from components.unit_state import UnitState, State
from camera import Camera
from game_constants import gc
from components.visual_link import VisualLink
from visuals import create_visual_spritesheet


class RenderingProcessor(esper.Processor):
    """
    Processor responsible for rendering entities.
    """

    def __init__(self, screen: pygame.Surface, camera: Camera, manager: pygame_gui.UIManager):
        self.screen = screen
        self.camera = camera
        self.manager = manager

    def _get_rect_for_circle(self, center_x: float, center_y: float, radius: float) -> tuple[float, float, float, float]:
        """
        Calculate the bounding rect for a circle in world coordinates.

        Args:
            center_x: X coordinate of circle center in world space
            center_y: Y coordinate of circle center in world space
            radius: Radius of the circle in world space

        Returns:
            Tuple of (min_x, min_y, width, height) defining the circle's bounding box
        """
        return (
            center_x - radius,
            center_y - radius,
            radius * 2,
            radius * 2
        )

    def _draw_circle(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        fill_color: Optional[tuple[int, int, int, int]] = None,
        outline_color: Optional[tuple[int, int, int, int]] = None
    ) -> None:
        """
        Draw a circle with optional fill and outline colors.

        Args:
            center_x: X coordinate of circle center in world space
            center_y: Y coordinate of circle center in world space
            radius: Radius of the circle in world space
            fill_color: Optional RGBA tuple for the circle fill
            outline_color: Optional RGBA tuple for the circle outline
        """
        world_rect = self._get_rect_for_circle(center_x, center_y, radius)
        if self.camera.is_box_off_screen(*world_rect):
            return

        screen_pos, screen_size = self.camera.world_to_screen_rect(world_rect)
        surface = pygame.Surface(screen_size, pygame.SRCALPHA)
        center = (screen_size[0]/2, screen_size[1]/2)
        radius_screen = radius * self.camera.scale
        
        if fill_color is not None:
            pygame.draw.circle(surface, fill_color, center, radius_screen)
        if outline_color is not None:
            pygame.draw.circle(surface, outline_color, center, radius_screen, 1)
        
        self.screen.blit(surface, screen_pos)

    def draw_sprite_sheet(self, sprite_sheet: SpriteSheet) -> None:
        """
        Draw a sprite sheet at the given world position.
        
        Args:
            sprite_sheet: The sprite sheet to draw
        """
        # Skip if sprite is completely off screen
        if self.camera.is_box_off_screen(
            sprite_sheet.rect.left,
            sprite_sheet.rect.top,
            sprite_sheet.rect.width,
            sprite_sheet.rect.height
        ):
            return

        rect_topleft = sprite_sheet.rect.topleft
        rect_width = sprite_sheet.rect.width
        rect_height = sprite_sheet.rect.height
        new_top_left = self.camera.world_to_screen(rect_topleft[0], rect_topleft[1])
        new_rect = pygame.Rect(new_top_left, (rect_width * self.camera.scale, rect_height * self.camera.scale))

        # Scale the sprite if needed
        if self.camera.scale != 1.0:
            scaled_size = (
                int(sprite_sheet.rect.width * self.camera.scale),
                int(sprite_sheet.rect.height * self.camera.scale)
            )
            scaled_image = pygame.transform.scale(sprite_sheet.image, scaled_size)
            self.screen.blit(scaled_image, new_rect)
        else:
            self.screen.blit(sprite_sheet.image, new_rect)

    def process(self, dt: float):
        # Draw all auras
        for ent, (aura, position) in esper.get_components(Aura, Position):
            if aura.owner_condition.check(aura.owner):
                self._draw_circle(
                    position.x,
                    position.y,
                    aura.radius,
                    fill_color=(*aura.color, 25),
                    outline_color=(*aura.color, 120)
                )

        # Draw visual links
        for ent, (visual_link,) in esper.get_components(VisualLink):
            if not esper.entity_exists(visual_link.other_entity):
                continue
                
            start_pos = esper.component_for_entity(ent, Position)
            end_pos = esper.component_for_entity(visual_link.other_entity, Position)
            
            # Calculate angle between start and end
            dx = end_pos.x - start_pos.x
            dy = end_pos.y - start_pos.y
            angle = math.atan2(dy, dx)
            
            # Calculate distance between start and end
            distance = math.sqrt(dx**2 + dy**2)
            
            # Calculate number of tiles needed
            num_tiles = int(distance / visual_link.tile_size)
            
            # Create sprite sheet once and rotate it
            sprite_sheet = create_visual_spritesheet(visual=visual_link.visual)
            sprite_sheet.update_frame(AnimationType.IDLE, 0)
            sprite_sheet.image = pygame.transform.rotate(sprite_sheet.image, -math.degrees(angle))
            
            # Draw each tile
            for i in range(num_tiles):
                # Calculate position of this tile
                t = i / num_tiles
                x = start_pos.x + dx * t
                y = start_pos.y + dy * t
                
                # Position the sprite
                sprite_sheet.rect.center = (x, y)
                
                # Draw the sprite
                self.draw_sprite_sheet(sprite_sheet)
                screen_pos = self.camera.world_to_screen(x, y)

        # Draw range indicators on focused units
        for ent, (range_indicator, position, _) in esper.get_components(RangeIndicator, Position, Focus):
            for range_value in range_indicator.ranges:
                self._draw_circle(
                    position.x,
                    position.y,
                    range_value,
                    fill_color=None,
                    outline_color=(200, 200, 200, 120)
                )

        # Get all entities with necessary components
        entities = esper.get_components(Position, SpriteSheet)

        # Sort entities based on their y-coordinate (higher y-value means lower on screen)
        sorted_entities = sorted(entities, key=lambda e: (e[1][1].layer, e[1][0].y))
        
        for ent, (pos, sprite_sheet) in sorted_entities:
            # Draw the sprite
            self.draw_sprite_sheet(sprite_sheet)

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
                # Draw hitbox
                # pygame.draw.rect(
                #     self.screen,
                #     (255, 255, 255),
                #     self.camera.world_to_screen_rect(
                #         (
                #             pos.x - hitbox.width/2,
                #             pos.y - hitbox.height/2,
                #             hitbox.width,
                #             hitbox.height
                #         )
                #     ),
                #     1
                # )
                if unit_state.state != State.DEAD and health.current < health.maximum:
                    self.draw_health_bar(pos, health, team, hitbox)
                
                # Draw item placement indicators if unit can have items
                if esper.has_component(ent, CanHaveItem):
                    self.draw_item_placement_indicator(pos, hitbox, team, ent)
                
                # Draw item indicators if unit has items
                if esper.has_component(ent, ItemComponent):
                    item_component = esper.component_for_entity(ent, ItemComponent)
                    if item_component.items:  # If unit has any items
                        self.draw_item_indicators(pos, item_component, hitbox, team, health)

        def draw_dashed_line(surface, color, start_pos, end_pos, width=1, dash_length=10, gap_length=5, t=0):
            start = pygame.Vector2(start_pos)
            end = pygame.Vector2(end_pos)
            direction = end - start
            distance = direction.length()

            if distance == 0:
                return  # Avoid division by zero

            direction.normalize_ip()
            pattern_length = dash_length + gap_length

            # Adjust t to loop within the pattern length
            t = t % pattern_length

            # Determine if we start with a dash or a gap based on t
            if t < dash_length:
                # Start with a partial dash
                dash_start = start
                dash_end = start + direction * min(dash_length - t, distance)
                pygame.draw.aaline(surface, color, dash_start, dash_end, width)
                current_pos = dash_length + gap_length - t
            else:
                current_pos = pattern_length - t

            while current_pos < distance:
                dash_start = start + direction * current_pos
                dash_end = start + direction * min(current_pos + dash_length, distance)
                pygame.draw.aaline(surface, color, dash_start, dash_end, width)
                current_pos += pattern_length

        def draw_arrow(
            start_x: float,
            start_y: float,
            end_x: float,
            end_y: float,
            color: tuple[int, int, int, int]
        ) -> None:
            start = pygame.Vector2(start_x, start_y)
            end = pygame.Vector2(end_x, end_y)
            direction = end - start
            distance = max(gc.TARGET_PREVIEW_GAP_DISTANCE, direction.length())
            
            # Get normalized direction vector
            direction = direction / distance
            
            # Get perpendicular vector for shift
            perp = pygame.Vector2(-direction.y, direction.x)
            shift = perp * gc.TARGET_PREVIEW_SHIFT
            
            # Calculate arrow body and head positions
            arrow_body = start + direction * gc.TARGET_PREVIEW_GAP_DISTANCE * self.camera.scale + shift
            arrow_head = start + direction * (distance - gc.TARGET_PREVIEW_GAP_DISTANCE * self.camera.scale) + shift
            draw_dashed_line(
                self.screen,
                color,
                arrow_body,
                arrow_head,
                width=1,
                dash_length=gc.TARGET_PREVIEW_DASH_LENGTH,
                gap_length=gc.TARGET_PREVIEW_GAP_LENGTH,
                t=-pygame.time.get_ticks() / gc.TARGET_PREVIEW_TICK_RATE
            )

        # Draw arrows from focused units to their targets
        for ent, (destination, position, team, _) in esper.get_components(Destination, Position, Team, Focus):
            target = destination.target_strategy.target
            if target is not None and esper.entity_exists(target):
                target_position = esper.component_for_entity(target, Position)
                screen_pos = self.camera.world_to_screen(position.x, position.y)
                target_screen_pos = self.camera.world_to_screen(target_position.x, target_position.y)
                draw_arrow(
                    start_x=screen_pos[0],
                    start_y=screen_pos[1],
                    end_x=target_screen_pos[0],
                    end_y=target_screen_pos[1],
                    color=gc.TEAM1_COLOR if team.type == TeamType.TEAM1 else gc.TEAM2_COLOR
                )
        
        # Draw arrows from units targetting focused units
        for ent, (destination, position, team) in esper.get_components(Destination, Position, Team):
            target = destination.target_strategy.target
            if target is not None and esper.entity_exists(target):
                if esper.has_component(target, Focus):
                    target_position = esper.component_for_entity(target, Position)
                    screen_pos = self.camera.world_to_screen(position.x, position.y)
                    target_screen_pos = self.camera.world_to_screen(target_position.x, target_position.y)
                    draw_arrow(
                        start_x=screen_pos[0],
                        start_y=screen_pos[1],
                        end_x=target_screen_pos[0],
                        end_y=target_screen_pos[1],
                        color=gc.TEAM1_COLOR if team.type == TeamType.TEAM1 else gc.TEAM2_COLOR
                    )
        
        # Clear focus on all units
        for ent, (focus,) in esper.get_components(Focus):
            esper.remove_component(ent, Focus)

    def _calculate_health_bar_position(self, pos: Position, hitbox: Hitbox) -> tuple[float, float, float, float]:
        """Calculate the position and dimensions of the health bar.
        
        Returns:
            tuple: (x, y, width, height) in screen coordinates
        """
        bar_width = 20 * self.camera.scale
        bar_height = 5 * self.camera.scale  # pixels
        bar_y_offset = 8 * self.camera.scale  # pixels above the unit's hitbox

        # Get screen position
        screen_pos = self.camera.world_to_screen(pos.x, pos.y)
        
        # Position the health bar above the hitbox
        # Bottom of health bar is at a fixed distance above the unit's hitbox
        bar_x = screen_pos[0] - bar_width // 2
        bar_y = screen_pos[1] - (hitbox.height * self.camera.scale)/2 - bar_y_offset - bar_height

        return bar_x, bar_y, bar_width, bar_height

    def draw_health_bar(self, pos: Position, health: Health, team: Team, hitbox: Hitbox):
        """Draw a health bar above the entity."""
        bar_x, bar_y, bar_width, bar_height = self._calculate_health_bar_position(pos, hitbox)
        bar_pos = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

        # Draw the background (empty health bar)
        pygame.draw.rect(self.screen, (64, 64, 64), bar_pos)

        # Draw the filled portion of the health bar
        fill_width = int(bar_width * health.current / health.maximum)
        fill_color = tuple(gc.TEAM1_COLOR) if team.type == TeamType.TEAM1 else tuple(gc.TEAM2_COLOR)
        pygame.draw.rect(self.screen, fill_color, (bar_pos.x, bar_pos.y, fill_width, bar_height))

        # Draw the border of the health bar
        pygame.draw.rect(self.screen, (192, 192, 192), bar_pos, 1)

    def draw_item_indicators(self, pos: Position, item_component: 'ItemComponent', hitbox: 'Hitbox', team: 'Team', health: 'Health') -> None:
        """Draw small indicators showing that a unit has items equipped."""
        screen_pos = self.camera.world_to_screen(pos.x, pos.y)
        
        bar_x, bar_y, bar_width, bar_height = self._calculate_health_bar_position(pos, hitbox)

        # Calculate position for item indicators (above the unit)
        indicator_size = 10 * self.camera.scale
        indicator_spacing = 2 * self.camera.scale
        total_width = len(item_component.items) * (indicator_size + indicator_spacing) - indicator_spacing
        start_x = screen_pos[0] - total_width // 2
        
        # Check if health bar is being displayed (unit is not at full health)
        health_bar_displayed = health.current < health.maximum
        
        if health_bar_displayed:
            # Position above the health bar
            start_y = bar_y - indicator_size - 3 * self.camera.scale  # Above the health bar
        else:
            # Position exactly where the health bar would be (replace health bar position)
            start_y = bar_y  # Same Y position as health bar
        
        # Draw a small square for each item
        for i, item_type in enumerate(item_component.items):
            x = start_x + i * (indicator_size + indicator_spacing)
            y = start_y
            
            # Use team color for item indicators
            color = tuple(gc.TEAM1_COLOR) if team.type == TeamType.TEAM1 else tuple(gc.TEAM2_COLOR)
            
            # Draw filled square
            pygame.draw.rect(self.screen, color, (x, y, indicator_size, indicator_size))
            # Draw border
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, indicator_size, indicator_size), 1)

    def draw_item_placement_indicator(self, pos: Position, hitbox: Hitbox, team: Team, entity_id: int) -> None:
        """Draw visual indicator for item placement on a unit."""
        screen_pos = self.camera.world_to_screen(pos.x, pos.y)
        radius = (hitbox.width ** 2 + hitbox.height ** 2) ** 0.5
        
        # Check if this unit is being hovered (simplified check)
        # We'll use a basic mouse position check since we don't have access to the hover logic here
        mouse_pos = pygame.mouse.get_pos()
        mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
        distance = ((pos.x - mouse_world_pos[0]) ** 2 + (pos.y - mouse_world_pos[1]) ** 2) ** 0.5
        is_hovered = distance < radius * 0.8  # Rough hover detection
        
        # Choose color based on hover state
        if is_hovered:
            color = (255, 255, 0)  # Bright yellow for hovered unit
            width = 3
        else:
            color = (0, 255, 0)  # Green for valid targets
            width = 2
        
        # Draw a single circle to indicate valid target
        pygame.draw.circle(
            self.screen, 
            color, 
            screen_pos, 
            (radius * self.camera.scale) * 0.7, 
            width=width
        )
        

