"""
OpenGL utility functions for drawing primitives.

This module contains helper functions for drawing basic shapes using OpenGL,
providing a consistent interface for all OpenGL drawing operations.
"""

import math
from typing import List, Tuple, Dict, Optional
import OpenGL.GL as gl
import shapely
import pygame
from weakref import WeakKeyDictionary


def gl_draw_line(start: Tuple[float, float], end: Tuple[float, float], color: Tuple[int, int, int], width: int = 1) -> None:
    """Draw a line using OpenGL.
    
    Args:
        start: Starting point (x, y)
        end: Ending point (x, y)
        color: RGB color tuple (0-255)
        width: Line width in pixels
    """
    gl.glColor3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    gl.glLineWidth(width)
    gl.glBegin(gl.GL_LINES)
    gl.glVertex2f(start[0], start[1])
    gl.glVertex2f(end[0], end[1])
    gl.glEnd()


def gl_draw_polygon(points: List[Tuple[float, float]], color: Tuple[int, int, int]) -> None:
    """Draw a filled polygon using OpenGL.
    
    Args:
        points: List of (x, y) coordinates forming the polygon
        color: RGB color tuple (0-255)
    """
    gl.glColor3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    gl.glBegin(gl.GL_POLYGON)
    for x, y in points:
        gl.glVertex2f(x, y)
    gl.glEnd()


def gl_draw_circle(center_x: float, center_y: float, radius: float, color: Tuple[int, int, int, int], filled: bool = True) -> None:
    """Draw a circle using OpenGL.
    
    Args:
        center_x: X coordinate of circle center
        center_y: Y coordinate of circle center
        radius: Circle radius
        color: RGBA color tuple (0-255)
        filled: Whether to fill the circle or just draw outline
    """
    # Set color with alpha
    gl.glColor4f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0)
    
    # Number of segments for smooth circle
    segments = max(8, int(radius * 0.5))  # More segments for larger circles
    
    if filled:
        # Draw filled circle using triangle fan
        gl.glBegin(gl.GL_TRIANGLE_FAN)
        gl.glVertex2f(center_x, center_y)  # Center vertex
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            gl.glVertex2f(x, y)
        gl.glEnd()
    else:
        # Draw circle outline using line loop
        gl.glBegin(gl.GL_LINE_LOOP)
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            gl.glVertex2f(x, y)
        gl.glEnd()


def gl_draw_rect(x: float, y: float, width: float, height: float, color: Tuple[int, int, int, int], filled: bool = True) -> None:
    """Draw a rectangle using OpenGL.
    
    Args:
        x: Left edge X coordinate
        y: Top edge Y coordinate
        width: Rectangle width
        height: Rectangle height
        color: RGBA color tuple (0-255)
        filled: Whether to fill the rectangle or just draw outline
    """
    gl.glColor4f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0)
    
    if filled:
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x + width, y)
        gl.glVertex2f(x + width, y + height)
        gl.glVertex2f(x, y + height)
        gl.glEnd()
    else:
        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x + width, y)
        gl.glVertex2f(x + width, y + height)
        gl.glVertex2f(x, y + height)
        gl.glEnd()


def gl_draw_shapely_polygon(polygon: shapely.Polygon, color: Tuple[int, int, int], alpha: int = 255) -> None:
    """Draw a shapely polygon using OpenGL triangulation.
    
    Args:
        polygon: Shapely Polygon object
        color: RGB color tuple (0-255)
        alpha: Alpha value (0-255)
    """
    coords = list(polygon.exterior.coords[:-1])  # Remove duplicate last point
    
    if len(coords) < 3:
        return
    
    # Convert color to OpenGL format with alpha
    gl_color = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, alpha / 255.0)
    gl.glColor4f(gl_color[0], gl_color[1], gl_color[2], gl_color[3])
    
    # Simple fan triangulation for convex polygons
    # For more complex polygons, we'd need proper triangulation
    gl.glBegin(gl.GL_TRIANGLE_FAN)
    for x, y in coords:
        gl.glVertex2f(x, y)
    gl.glEnd()


def gl_draw_lines(points: List[Tuple[float, float]], color: Tuple[int, int, int], width: int = 1, closed: bool = False) -> None:
    """Draw connected line segments using OpenGL.
    
    Args:
        points: List of (x, y) coordinates to connect
        color: RGB color tuple (0-255)
        width: Line width in pixels
        closed: Whether to connect the last point back to the first
    """
    if len(points) < 2:
        return
    
    gl.glColor3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    gl.glLineWidth(width)
    
    if closed:
        gl.glBegin(gl.GL_LINE_LOOP)
    else:
        gl.glBegin(gl.GL_LINE_STRIP)
    
    for x, y in points:
        gl.glVertex2f(x, y)
    
    gl.glEnd()


def gl_draw_star(center_x: float, center_y: float, outer_radius: float, inner_radius: float, num_points: int, color: Tuple[int, int, int]) -> None:
    """Draw a filled star using OpenGL triangles.
    
    Args:
        center_x: X coordinate of star center
        center_y: Y coordinate of star center
        outer_radius: Radius to outer points
        inner_radius: Radius to inner points
        num_points: Number of star points (typically 5)
        color: RGB color tuple (0-255)
    """
    gl.glColor3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    
    # Calculate star points
    points = []
    for i in range(num_points * 2):  # Alternating outer and inner points
        angle = (i * math.pi) / num_points  # Angle between points
        if i % 2 == 0:  # Outer point
            radius = outer_radius
        else:  # Inner point
            radius = inner_radius
        
        x = center_x + radius * math.cos(angle - math.pi / 2)  # Rotate -90 degrees to point up
        y = center_y + radius * math.sin(angle - math.pi / 2)
        points.append((x, y))
    
    # Draw triangles from center to each edge of the star
    gl.glBegin(gl.GL_TRIANGLES)
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        
        # Triangle from center to current point to next point
        gl.glVertex2f(center_x, center_y)  # Center
        gl.glVertex2f(points[i][0], points[i][1])  # Current point
        gl.glVertex2f(points[next_i][0], points[next_i][1])  # Next point
    
    gl.glEnd()


# Texture caching - maps pygame surface objects to OpenGL texture IDs
_texture_cache: WeakKeyDictionary[pygame.Surface, int] = WeakKeyDictionary()


def surface_to_texture(surface: pygame.Surface) -> int:
    """Convert a pygame surface to an OpenGL texture.
    
    Args:
        surface: The pygame surface to convert
        
    Returns:
        OpenGL texture ID
    """
    # Check cache first
    if surface in _texture_cache:
        return _texture_cache[surface]
    
    # Convert surface to string format for OpenGL
    texture_data = pygame.image.tostring(surface, "RGBA", True)
    width, height = surface.get_size()
    
    # Generate and bind texture
    texture_id = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    
    # Set texture parameters
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    
    # Upload texture data
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        gl.GL_RGBA,
        width,
        height,
        0,
        gl.GL_RGBA,
        gl.GL_UNSIGNED_BYTE,
        texture_data
    )
    
    # Cache the texture
    _texture_cache[surface] = texture_id
    
    return texture_id


def delete_texture(texture_id: int) -> None:
    """Delete an OpenGL texture.
    
    Args:
        texture_id: The OpenGL texture ID to delete
    """
    gl.glDeleteTextures([texture_id])


def clear_texture_cache() -> None:
    """Clear all cached textures and free GPU memory."""
    for texture_id in _texture_cache.values():
        gl.glDeleteTextures([texture_id])
    _texture_cache.clear()


def gl_draw_sprite(
    surface: pygame.Surface,
    x: float,
    y: float,
    width: float,
    height: float,
    alpha: float = 1.0
) -> None:
    """Draw a pygame surface as an OpenGL textured quad.
    
    Args:
        surface: The pygame surface to draw
        x: Left edge X coordinate
        y: Top edge Y coordinate  
        width: Width to draw the sprite
        height: Height to draw the sprite
        alpha: Alpha transparency (0.0 to 1.0)
    """
    # Get or create texture
    texture_id = surface_to_texture(surface)
    
    # Enable texturing
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    
    # Set color with alpha
    gl.glColor4f(1.0, 1.0, 1.0, alpha)
    
    # Draw textured quad with flipped texture coordinates to match pygame coordinate system
    gl.glBegin(gl.GL_QUADS)
    gl.glTexCoord2f(0.0, 1.0)  # Top-left of texture
    gl.glVertex2f(x, y)
    gl.glTexCoord2f(1.0, 1.0)  # Top-right of texture
    gl.glVertex2f(x + width, y)
    gl.glTexCoord2f(1.0, 0.0)  # Bottom-right of texture
    gl.glVertex2f(x + width, y + height)
    gl.glTexCoord2f(0.0, 0.0)  # Bottom-left of texture
    gl.glVertex2f(x, y + height)
    gl.glEnd()
    
    # Disable texturing
    gl.glDisable(gl.GL_TEXTURE_2D)