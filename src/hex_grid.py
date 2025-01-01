"""
Hex grid utilities for converting between hex and world coordinates.

This module provides functions for working with a pointy-topped hexagonal grid system,
including coordinate conversions and geometry calculations.
"""

import math
from typing import List, Tuple
from game_constants import gc

def axial_to_world(q: int, r: int, 
                  hex_size: float = gc.HEX_SIZE,
                  center_x: float = 0, 
                  center_y: float = 0) -> Tuple[float, float]:
    """
    Convert axial hex coordinates to world coordinates (center of the hex cell).
    
    Args:
        q: The q coordinate in the axial system (roughly corresponds to x)
        r: The r coordinate in the axial system (roughly corresponds to y)
        hex_size: The size of a hex (distance from center to corner), defaults to game constant
        center_x: World x coordinate of the grid center
        center_y: World y coordinate of the grid center
        
    Returns:
        Tuple of (x, y) world coordinates
    """
    # Pointy-top hex coordinate conversion
    x = hex_size * (math.sqrt(3) * q + math.sqrt(3)/2 * r)
    y = hex_size * (3.0/2 * r)
    
    return (x + center_x, y + center_y)

def world_to_axial(x: float, y: float, 
                  hex_size: float = gc.HEX_SIZE,
                  center_x: float = 0, 
                  center_y: float = 0) -> Tuple[int, int]:
    """
    Convert world coordinates to axial hex coordinates.
    
    Args:
        x: World x coordinate
        y: World y coordinate
        hex_size: The size of a hex (distance from center to corner), defaults to game constant
        center_x: World x coordinate of the grid center
        center_y: World y coordinate of the grid center
        
    Returns:
        Tuple of (q, r) axial coordinates
    """
    # Adjust for grid center
    x = x - center_x
    y = y - center_y
    
    # For pointy-topped hexes
    q = (math.sqrt(3) * x - y) / (3 * hex_size)
    r = (2 * y) / (3 * hex_size)
    
    # Round to nearest hex
    return hex_round(q, r)

def hex_round(q: float, r: float) -> Tuple[int, int]:
    """
    Round floating point axial coordinates to the nearest hex cell.
    
    Args:
        q: Floating point q coordinate
        r: Floating point r coordinate
        
    Returns:
        Tuple of (q, r) as integers identifying the nearest hex
    """
    # Convert to cube coordinates
    x = q
    z = r
    y = -x - z
    
    # Round cube coordinates
    rx = round(x)
    ry = round(y)
    rz = round(z)
    
    # Adjust for rounding errors
    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)
    
    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry
        
    # Convert back to axial
    return (rx, rz)

def get_hex_vertices(q: int, r: int, 
                    hex_size: float = gc.HEX_SIZE) -> List[Tuple[float, float]]:
    """
    Get the vertices of a hexagon in world coordinates.
    
    Args:
        q: The q coordinate in the axial system
        r: The r coordinate in the axial system
        hex_size: The size of a hex (distance from center to corner), defaults to game constant
        
    Returns:
        List of (x, y) tuples representing vertex positions in world space
    """
    # Convert hex coordinates to world coordinates
    x, y = axial_to_world(q, r, hex_size)
    
    vertices = []
    for i in range(6):
        angle_deg = 60 * i + 30  # Start at 30 degrees for pointy-top
        angle_rad = math.pi / 180 * angle_deg
        vertex_x = x + hex_size * math.cos(angle_rad)
        vertex_y = y + hex_size * math.sin(angle_rad)
        vertices.append((vertex_x, vertex_y))
    return vertices

def get_hex_bounds(q: int, r: int, 
                  hex_size: float = gc.HEX_SIZE) -> Tuple[float, float, float, float]:
    """
    Get the bounding box of a hexagon in world coordinates.
    
    Args:
        q: The q coordinate in the axial system
        r: The r coordinate in the axial system
        hex_size: The size of a hex (distance from center to corner), defaults to game constant
        
    Returns:
        Tuple of (min_x, min_y, width, height) defining the bounding rectangle
    """
    # For a pointy-topped hex:
    # width = 2 * hex_size * cos(30°) = sqrt(3) * hex_size
    # height = 2 * hex_size
    width = math.sqrt(3) * hex_size
    height = 2 * hex_size
    
    # Calculate top-left corner
    x, y = axial_to_world(q, r, hex_size)
    min_x = x - width/2
    min_y = y - height/2
    
    return (min_x, min_y, width, height) 

def get_edge_vertices(edge: frozenset[tuple[int, int]]) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Get the vertices for a hex edge in world coordinates.
    
    Args:
        edge: A frozenset containing exactly two hex coordinates that share an edge
        
    Returns:
        A tuple of two (x, y) world coordinates representing the edge vertices
    """
    if len(edge) != 2:
        raise ValueError("Edge must contain exactly two hex coordinates")
    
    # Convert both hex coordinates to world coordinates
    coords = list(edge)
    
    # Get all vertices for both hexes
    vertices1 = get_hex_vertices(*coords[0])
    vertices2 = get_hex_vertices(*coords[1])
    
    # Find the two vertices that are closest to both hex centers
    # These will be the shared vertices of the edge
    shared_vertices = []
    for v1 in vertices1:
        for v2 in vertices2:
            # Check if vertices are the same (within floating point error)
            if abs(v1[0] - v2[0]) < 0.001 and abs(v1[1] - v2[1]) < 0.001:
                shared_vertices.append(v1)
                
    if len(shared_vertices) != 2:
        raise ValueError("Could not find exactly 2 shared vertices")
        
    return tuple(shared_vertices)

NEIGHBOR_OFFSETS = [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]

def hex_neighbors(coords: Tuple[int,int]) -> List[Tuple[int,int]]:
    """
    Return the axial coordinates of the six neighbors for the given hex cell.
    
    :param coords: Axial coords (q, r)
    """
    q, r = coords
    return [(q+dq, r+dr) for dq, dr in NEIGHBOR_OFFSETS]

def get_edges_for_hexes(hex_coords: set[Tuple[int, int]]) -> set[frozenset[Tuple[int, int]]]:
    """
    Get all edges that border any of the given hex coordinates.
    
    Args:
        hex_coords: Set of hex coordinates in axial format (q, r)
        
    Returns:
        Set of edges, where each edge is a frozenset of two hex coordinates
    """
    edges = set()
    for coords in hex_coords:
        for neighbor in hex_neighbors(coords):
            edges.add(frozenset([coords, neighbor]))
    return edges
