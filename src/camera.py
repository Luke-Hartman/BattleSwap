import numpy as np
import pygame
from shapely import Polygon
import shapely
from typing import Optional
import math
from game_constants import gc

class Camera:
    def __init__(self, world_x: float = 0.0, world_y: float = 0.0, zoom: float = 1.0):
        """Initialize a Camera object.
        
        Args:
            world_x: X coordinate in world space to center the camera on
            world_y: Y coordinate in world space to center the camera on
            zoom: Initial zoom level
        """
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        self._rect = pygame.Rect(
            world_x - screen_width/2,
            world_y - screen_height/2,
            screen_width,
            screen_height
        )
        self._base_width = screen_width
        self._base_height = screen_height
        self.speed = 10
        self._zoom_levels = [1/6, 1/5, 1/4, 1/3, 1/2, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        self._zoom = 1.0
        self._set_zoom(zoom)

        # Animation state
        self._moving = False
        self._start_x = 0.0
        self._start_y = 0.0
        self._start_zoom = 0.0
        self._end_x = 0.0
        self._end_y = 0.0
        self._end_zoom = 0.0
        self._duration = 0.0
        self._elapsed = 0.0
        self._distance = 0.0

    @property
    def zoom(self) -> float:
        """The current zoom level. 1.0 is the default view."""
        return self._zoom

    def _set_zoom(self, zoom: float) -> None:
        """
        Set zoom to a specific value, updating the view rectangle. When zooming in,
        maintains the world position under the mouse cursor.

        Args:
            zoom: The zoom level to set. Must be one of the predefined zoom levels.

        Raises:
            KeyError: If the zoom value is not in the predefined zoom levels.
        """
        zoom = max(self._zoom_levels[0], min(self._zoom_levels[-1], zoom))
        old_zoom = self._zoom
        # Only maintain mouse position if zooming in
        if zoom > old_zoom:
            # Get current mouse position in screen coordinates
            mouse_x, mouse_y = pygame.mouse.get_pos()
            old_world_x, old_world_y = self.screen_to_world(mouse_x, mouse_y)
        
        # Update zoom and rectangle
        self._zoom = zoom
        center = self._rect.center
        self._rect.width = int(self._base_width / self._zoom)
        self._rect.height = int(self._base_height / self._zoom)
        self._rect.center = center
        
        # Adjust camera position when zooming in
        if zoom > old_zoom:
            new_world_x, new_world_y = self.screen_to_world(mouse_x, mouse_y)
            self.x += (old_world_x - new_world_x)
            self.y += (old_world_y - new_world_y)

    @property
    def x(self) -> int:
        """The x-coordinate of the camera's top-left corner in the world."""
        return self._rect.x

    @x.setter
    def x(self, value: int) -> None:
        self._rect.x = value

    @property
    def y(self) -> int:
        """The y-coordinate of the camera's top-left corner in the world."""
        return self._rect.y

    @y.setter
    def y(self, value: int) -> None:
        self._rect.y = value

    @property
    def width(self) -> int:
        """The width of the camera view."""
        return self._rect.width

    @width.setter
    def width(self, value: int) -> None:
        self._rect.width = value

    @property
    def height(self) -> int:
        """The height of the camera view."""
        return self._rect.height

    @height.setter
    def height(self, value: int) -> None:
        self._rect.height = value
    
    @property
    def scale(self) -> float:
        return self._zoom

    @property
    def centerx(self) -> float:
        """The x-coordinate of the camera's center in world coordinates."""
        return self._rect.centerx

    @centerx.setter
    def centerx(self, value: float) -> None:
        self._rect.centerx = value

    @property
    def centery(self) -> float:
        """The y-coordinate of the camera's center in world coordinates."""
        return self._rect.centery

    @centery.setter
    def centery(self, value: float) -> None:
        self._rect.centery = value

    def process_event(self, event: pygame.event.Event) -> bool:
        """Process a single event and return whether it was consumed."""
        if self._moving:
            return True
            
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                # Zoom in - find next highest zoom level
                higher_zooms = [z for z in self._zoom_levels if z > self._zoom]
                next_zoom = min(higher_zooms) if higher_zooms else self._zoom
            else:
                # Zoom out - find next lowest zoom level
                lower_zooms = [z for z in self._zoom_levels if z < self._zoom]
                next_zoom = max(lower_zooms) if lower_zooms else self._zoom
            self._set_zoom(next_zoom)
            return True
        if event.type in [pygame.KEYDOWN, pygame.KEYUP] and event.key in [
                pygame.K_LEFT, pygame.K_a,
                pygame.K_RIGHT, pygame.K_d,
                pygame.K_UP, pygame.K_w,
                pygame.K_DOWN, pygame.K_s
            ]:
            return True
        return False
    
    def update(self, time_delta: float) -> None:
        """Update the camera position based on input and animation."""
        if self._moving:
            # Advance time
            self._elapsed += time_delta
            t = self._elapsed / self._duration

            if t >= 1.0:
                # We've reached or passed the end; snap to final
                self.centerx = self._end_x
                self.centery = self._end_y
                self._set_zoom(self._end_zoom)
                self._moving = False
                return

            # SmoothSteper and derivative
            def smootherstep(x):
                return 6*x**5 - 15*x**4 + 10*x**3

            def dsmootherstep(x):
                return 30*x**4 - 60*x**3 + 30*x**2
            
            def ease_out_and_in(u: float, p: float) -> float:
                # Starts and ends at 1, but rapidly goes to 0 in the middle
                return (1 - u)**p + u**p

            et = smootherstep(t)
            etp = dsmootherstep(t)

            # Interpolate position
            dx = self._end_x - self._start_x
            dy = self._end_y - self._start_y
            self.centerx = self._start_x + dx * et
            self.centery = self._start_y + dy * et

            # Logarithmic zoom interpolation
            log_start = math.log2(self._start_zoom)
            log_end = math.log2(self._end_zoom)
            
            # Calculate the interpolated log zoom
            log_zoom_t = (
                log_start
                + (log_end - log_start) * t  # Linear interpolation in log space
            )

            # Zoom based on velocity
            world_velocity = (dx**2 + dy**2)**0.5 * abs(etp)
            if world_velocity < 1e-9:
                world_velocity = 1e-9
            zoom_v = gc.CAMERA_ANIMATION_ZOOM_VELOCITY_SCALE / world_velocity
            log_zoom_v = math.log2(zoom_v)

            def softmin(x: float, y: float, intensity: float) -> float:
                ex = math.exp(-x * intensity)
                ey = math.exp(-y * intensity)
                return (x * ex + y * ey) / (ex + ey)

            log_zoom_blend = (
                ease_out_and_in(t, gc.CAMERA_ANIMATION_EASE_POWER)*log_zoom_t 
                + (1-ease_out_and_in(t, gc.CAMERA_ANIMATION_EASE_POWER))
                *softmin(log_zoom_v, log_zoom_t, gc.CAMERA_ANIMATION_SOFTMIN_INTENSITY)
            )
            zoom_blend = 2.0 ** log_zoom_blend
            self._set_zoom(zoom_blend)
        else:
            # Handle manual movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x -= self.speed / self.scale
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x += self.speed / self.scale
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.y -= self.speed / self.scale
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.y += self.speed / self.scale

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        """
        Transform world coordinates to screen coordinates.

        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space

        Returns:
            A tuple of (screen_x, screen_y) coordinates
        """
        # First translate relative to camera position
        rel_x = world_x - self.x
        rel_y = world_y - self.y
        
        # Then scale by zoom factor
        screen_x = rel_x * self._zoom
        screen_y = rel_y * self._zoom
        
        return (screen_x, screen_y)

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """
        Transform screen coordinates to world coordinates.

        Args:
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space

        Returns:
            A tuple of (world_x, world_y) coordinates
        """
        # First unscale by zoom factor
        rel_x = screen_x / self._zoom
        rel_y = screen_y / self._zoom
        
        # Then translate back to world position
        world_x = rel_x + self.x
        world_y = rel_y + self.y
        
        return (world_x, world_y)

    def is_box_off_screen(self, min_x: float, min_y: float, width: float, height: float) -> bool:
        """
        Check if a bounding box is completely off screen.

        Args:
            min_x: Left edge of the box in world coordinates
            min_y: Top edge of the box in world coordinates
            width: Width of the box in world coordinates
            height: Height of the box in world coordinates

        Returns:
            True if the box is completely off screen, False otherwise
        """
        # Convert box to screen coordinates
        screen_min_x, screen_min_y = self.world_to_screen(min_x, min_y)
        screen_max_x, screen_max_y = self.world_to_screen(min_x + width, min_y + height)
        
        return (screen_max_x < 0 or 
                screen_min_x > self._base_width or
                screen_max_y < 0 or 
                screen_min_y > self._base_height)

    def world_to_screen_rect(self, world_rect: tuple[float, float, float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
        """
        Transform a world-space rectangle to screen-space position and size.

        Args:
            world_rect: Tuple of (x, y, width, height) in world coordinates

        Returns:
            Tuple of (screen_pos, screen_size) where each is a tuple of (x, y)
        """
        screen_pos = self.world_to_screen(world_rect[0], world_rect[1])
        width = world_rect[2] * self._zoom
        height = world_rect[3] * self._zoom
        return (screen_pos, (width, height))

    def screen_to_world_rect(self, screen_rect: tuple[float, float, float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
        """
        Transform a screen-space rectangle to world-space position and size.

        Args:
            screen_rect: Tuple of (x, y, width, height) in screen coordinates

        Returns:
            Tuple of (world_pos, world_size) where each is a tuple of (x, y)
        """
        world_pos = self.screen_to_world(screen_rect[0], screen_rect[1])
        width = screen_rect[2] / self._zoom
        height = screen_rect[3] / self._zoom
        return (world_pos, (width, height))

    def get_screen_polygon(self, world_coords: bool = False) -> Polygon:
        """Returns the screen polygon in screen or world coordinates."""
        screen_polygon = Polygon([
            (0, 0),
            (self._base_width, 0),
            (self._base_width, self._base_height),
            (0, self._base_height)
        ])
        if world_coords:
            return self.screen_to_world_polygon(screen_polygon)
        return screen_polygon
    
    def world_to_screen_polygon(self, polygon: Polygon, clip: bool = True) -> Polygon:
        """Returns the world polygon in screen coordinates."""
        unclipped = shapely.transform(
            polygon, 
            lambda xy: np.array([
                self.world_to_screen(x, y) for x, y in xy
            ])
        )
        if clip:
            return self.get_screen_polygon().intersection(unclipped)
        return unclipped

    def screen_to_world_polygon(self, polygon: Polygon, clip: bool = True) -> Polygon:
        """Returns the screen polygon in world coordinates."""
        unclipped = shapely.transform(
            polygon, 
            lambda xy: np.array([
                self.screen_to_world(x, y) for x, y in xy
            ])
        )
        if clip:
            return self.get_screen_polygon(world_coords=True).intersection(unclipped)
        return unclipped

    def move(self, centerx: float, centery: float, zoom: float) -> None:
        """Start a smooth camera movement to the target position and zoom.
        
        Args:
            centerx: Target x position in world coordinates (center of view)
            centery: Target y position in world coordinates (center of view)
            zoom: Target zoom level (must be one of the allowed zoom levels)
        
        Raises:
            KeyError: If the zoom value is not in the predefined zoom levels
        """
        if zoom not in self._zoom_levels:
            raise KeyError(f"Zoom value {zoom} not in allowed zoom levels: {self._zoom_levels}")
        
        # Calculate distance
        dx = centerx - self.centerx
        dy = centery - self.centery
        d = (dx**2 + dy**2)**0.5

        # Calculate zoom ratio duration component using logarithmic scale
        log_zoom_ratio = abs(math.log2(zoom / self._zoom))
        T_zoom = gc.CAMERA_ANIMATION_ZOOM_DURATION_SCALE * log_zoom_ratio

        # Calculate distance-based duration component
        T_dist = gc.CAMERA_ANIMATION_DURATION_SCALE * (d ** gc.CAMERA_ANIMATION_DURATION_EXPONENT)

        if d < 1e-9 and abs(zoom - self._zoom) < 1e-9:
            # Distance and zoom change are effectively zero; just snap instantly
            self.centerx = centerx
            self.centery = centery
            self._zoom = zoom
            self._moving = False
            return

        T = (T_zoom**2 + T_dist**2)**0.5

        # Store animation state
        self._moving = True
        self._start_x = self.centerx
        self._start_y = self.centery
        self._start_zoom = self._zoom
        self._end_x = centerx
        self._end_y = centery
        self._end_zoom = zoom
        self._duration = T
        self._elapsed = 0.0
        self._distance = d


