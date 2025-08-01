"""
OpenGL utility functions for drawing primitives.

This module contains helper functions for drawing basic shapes using OpenGL,
providing a consistent interface for all OpenGL drawing operations.
"""

import math
from typing import List, Tuple
import OpenGL.GL as gl
import shapely


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