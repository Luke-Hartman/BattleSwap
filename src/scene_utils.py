"""Utility functions for scene rendering and management."""
from contextlib import contextmanager
from functools import lru_cache
from typing import Generator, List, Tuple, Optional
import esper
import pygame
import pygame.gfxdraw
import pygame_gui
import shapely
from battles import Battle
from camera import Camera
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.unit_type import UnitType, UnitTypeComponent
from game_constants import gc
from hex_grid import get_hex_vertices, axial_to_world
from components.team import Team, TeamType
from shapely.ops import nearest_points
from progress_manager import progress_manager

LARGE_NUMBER = 10000

def draw_grid(
    screen: pygame.Surface,
    camera: Camera,
    hex_coords: Tuple[int, int],
) -> None:
    """Draw a grid centered on the given hex coordinates.
    
    Args:
        screen: The pygame surface to draw on
        camera: Camera instance for coordinate transforms
        hex_coords: (q,r) axial coordinates of the hex to center on
    """
    # Convert hex coordinates to world coordinates using hex_grid utilities
    center_x, center_y = axial_to_world(*hex_coords)
    
    # Create hex polygon for clipping
    hex_vertices = get_hex_vertices(*hex_coords)
    hex_polygon = shapely.Polygon(hex_vertices)
    
    # Get the visible area in world coordinates
    screen_rect = screen.get_rect()
    top_left = camera.screen_to_world(screen_rect.left, screen_rect.top)
    bottom_right = camera.screen_to_world(screen_rect.right, screen_rect.bottom)
    
    # Calculate grid line ranges
    start_x = int(top_left[0] // gc.GRID_SIZE) * gc.GRID_SIZE
    end_x = int(bottom_right[0] // gc.GRID_SIZE + 1) * gc.GRID_SIZE
    start_y = int(top_left[1] // gc.GRID_SIZE) * gc.GRID_SIZE
    end_y = int(bottom_right[1] // gc.GRID_SIZE + 1) * gc.GRID_SIZE
    
    # Draw vertical lines
    for x in range(int(start_x), int(end_x), gc.GRID_SIZE):
        # Create line as shapely object
        line = shapely.LineString([(x, start_y), (x, end_y)])
        # Intersect with hex
        if line.intersects(hex_polygon):
            intersection = line.intersection(hex_polygon)
            if isinstance(intersection, shapely.LineString):
                # Check if this is a major grid line
                is_major = ((x - center_x) // gc.GRID_SIZE) % gc.MAJOR_GRID_INTERVAL == 0
                color = (150, 150, 150) if is_major else (75, 75, 75)
                width = 2 if is_major else 1
                
                # Convert intersection coordinates to screen space
                start_pos = camera.world_to_screen(intersection.coords[0][0], intersection.coords[0][1])
                end_pos = camera.world_to_screen(intersection.coords[-1][0], intersection.coords[-1][1])
                pygame.draw.line(screen, color, start_pos, end_pos, width)
    
    # Draw horizontal lines
    for y in range(int(start_y), int(end_y), gc.GRID_SIZE):
        # Create line as shapely object
        line = shapely.LineString([(start_x, y), (end_x, y)])
        # Intersect with hex
        if line.intersects(hex_polygon):
            intersection = line.intersection(hex_polygon)
            if isinstance(intersection, shapely.LineString):
                # Check if this is a major grid line
                is_major = ((y - center_y) // gc.GRID_SIZE) % gc.MAJOR_GRID_INTERVAL == 0
                color = (150, 150, 150) if is_major else (75, 75, 75)
                width = 2 if is_major else 1
                
                # Convert intersection coordinates to screen space
                start_pos = camera.world_to_screen(intersection.coords[0][0], intersection.coords[0][1])
                end_pos = camera.world_to_screen(intersection.coords[-1][0], intersection.coords[-1][1])
                pygame.draw.line(screen, color, start_pos, end_pos, width)
    
    # Draw center lines
    # Vertical center line
    center_line = shapely.LineString([(center_x, start_y), (center_x, end_y)])
    if center_line.intersects(hex_polygon):
        intersection = center_line.intersection(hex_polygon)
        if isinstance(intersection, shapely.LineString):
            start_pos = camera.world_to_screen(intersection.coords[0][0], intersection.coords[0][1])
            end_pos = camera.world_to_screen(intersection.coords[-1][0], intersection.coords[-1][1])
            pygame.draw.line(screen, (200, 200, 200), start_pos, end_pos, 3)
    
    # Horizontal center line
    center_line = shapely.LineString([(start_x, center_y), (end_x, center_y)])
    if center_line.intersects(hex_polygon):
        intersection = center_line.intersection(hex_polygon)
        if isinstance(intersection, shapely.LineString):
            start_pos = camera.world_to_screen(intersection.coords[0][0], intersection.coords[0][1])
            end_pos = camera.world_to_screen(intersection.coords[-1][0], intersection.coords[-1][1])
            pygame.draw.line(screen, (200, 200, 200), start_pos, end_pos, 3)

def snap_position_to_grid(x: float, y: float, hex_coords: Tuple[int, int]) -> tuple[float, float]:
    """Snap world coordinates to the nearest grid intersection.
    
    Args:
        x: World x coordinate
        y: World y coordinate
        hex_coords: (q,r) axial coordinates of the hex cell containing the grid
        
    Returns:
        Tuple of (x, y) world coordinates snapped to grid
    """
    # Get the hex center as the grid origin
    center_x, center_y = axial_to_world(*hex_coords)
    
    # Offset coordinates relative to hex center
    rel_x = x - center_x
    rel_y = y - center_y
    
    # Snap to grid
    snapped_x = round(rel_x / gc.GRID_SIZE) * gc.GRID_SIZE
    snapped_y = round(rel_y / gc.GRID_SIZE) * gc.GRID_SIZE
    
    # Convert back to world coordinates
    return (snapped_x + center_x, snapped_y + center_y)

def get_hovered_unit(camera: Camera) -> Optional[int]:
    """Return the entity ID of the unit under the mouse cursor.
    
    Args:
        camera: Camera instance for coordinate transforms
        
    Returns:
        Entity ID of the hovered unit, or None if no unit is hovered
    """
    mouse_pos = pygame.mouse.get_pos()
    world_mouse_pos = camera.screen_to_world(*mouse_pos)
    candidate_unit_id = None
    highest_y = -float('inf')
    for ent, (sprite, pos, _) in esper.get_components(SpriteSheet, Position, UnitTypeComponent):
        if sprite.rect.collidepoint(world_mouse_pos):
            relative_mouse_pos = (
                world_mouse_pos[0] - sprite.rect.x,
                world_mouse_pos[1] - sprite.rect.y
            )
            try:
                if sprite.image.get_at(relative_mouse_pos).a != 0:
                    if pos.y > highest_y:
                        highest_y = pos.y
                        candidate_unit_id = ent
            except IndexError:
                pass
    return candidate_unit_id

def get_placement_pos(
    battle_id: str,
    hex_coords: Tuple[int, int],
    camera: Camera,
    snap_to_grid: bool = False,
    required_team: Optional[TeamType] = None,
) -> Tuple[float, float]:
    """Get the world coordinates of the mouse cursor after applying legal placement area and snapping to grid."""
    screen_pos = pygame.mouse.get_pos()
    world_pos = camera.screen_to_world(*screen_pos)
    clipped_pos = clip_to_polygon(get_legal_placement_area(battle_id, hex_coords, required_team, include_units=True), *world_pos)
    if snap_to_grid:
        return snap_position_to_grid(clipped_pos[0], clipped_pos[1], hex_coords)
    return clipped_pos

def get_battlefield_polygon(hex_coords: Tuple[int, int]) -> shapely.Polygon:
    """Get the battlefield polygon for a hex."""
    return shapely.Polygon(get_hex_vertices(*hex_coords))

@lru_cache(maxsize=10)
def _get_legal_placement_area_helper(
    legal_area_without_units: shapely.Polygon,
    unit_positions: Tuple[Tuple[float, float]],
) -> shapely.Polygon:
    legal_area = legal_area_without_units
    for unit_pos in unit_positions:
        unit_circle = shapely.Point(unit_pos).buffer(gc.UNIT_PLACEMENT_MINIMUM_DISTANCE)
        legal_area = legal_area.difference(unit_circle)
    return legal_area

def get_legal_placement_area(
    battle_id: str,
    hex_coords: Tuple[int, int],
    required_team: Optional[TeamType] = None,
    include_units: bool = True,
) -> shapely.Polygon:
    """Get the legal placement area for a hex.
    
    Args:
        battle_id: ID of the battle to check
        hex_coords: (q,r) axial coordinates of the hex
        required_team: If provided, restrict to this team's side
        include_units: If True, also restrict placement around existing units

    Returns:
        Shapely polygon representing the legal placement area
    """    
    # Get hex center
    hex_center_x, _ = axial_to_world(*hex_coords)
    
    # Create battlefield polygon centered on hex
    battlefield = get_battlefield_polygon(hex_coords)
    
    # Create no man's land polygon
    no_mans_land = shapely.Polygon([
        (hex_center_x - gc.NO_MANS_LAND_WIDTH//2, -LARGE_NUMBER), 
        (hex_center_x - gc.NO_MANS_LAND_WIDTH//2, LARGE_NUMBER), 
        (hex_center_x + gc.NO_MANS_LAND_WIDTH//2, LARGE_NUMBER), 
        (hex_center_x + gc.NO_MANS_LAND_WIDTH//2, -LARGE_NUMBER)
    ])
    
    # Get base legal area
    legal_area = battlefield.difference(no_mans_land)
    
    # If team is specified, restrict to appropriate side
    if required_team is not None:
        # Create half-plane for team's side
        half_plane = shapely.Polygon([
            (hex_center_x, -LARGE_NUMBER),
            (hex_center_x, LARGE_NUMBER),
            (-LARGE_NUMBER if required_team == TeamType.TEAM1 else LARGE_NUMBER, LARGE_NUMBER),
            (-LARGE_NUMBER if required_team == TeamType.TEAM1 else LARGE_NUMBER, -LARGE_NUMBER)
        ])
        legal_area = legal_area.intersection(half_plane)

    # Remove a circle around every unit
    if include_units:
        unit_positions = []
        with use_world(battle_id):
            for _, (pos, _) in esper.get_components(Position, UnitTypeComponent):
                unit_positions.append((pos.x, pos.y))
        legal_area = _get_legal_placement_area_helper(legal_area, tuple(unit_positions))
    return legal_area

def get_center_line(hex_coords: Tuple[int, int]) -> shapely.LineString:
    """Get the center line of a hex."""
    hex_center_x, _ = axial_to_world(*hex_coords)
    return shapely.LineString([(hex_center_x, -LARGE_NUMBER), (hex_center_x, LARGE_NUMBER)]).intersection(
        get_battlefield_polygon(hex_coords)
    )

def clip_to_polygon(
    polygon: shapely.Polygon,
    x: float,
    y: float,
) -> Tuple[float, float]:
    point = shapely.Point(x, y)
    if polygon.contains(point):
        return (x, y)
    result = nearest_points(point, polygon)[1]
    return (result.x, result.y)

def is_drawable(polygon: shapely.Polygon) -> bool:
    """Check if a polygon has any area."""
    if isinstance(polygon, shapely.MultiPolygon):
        return all(is_drawable(p) for p in polygon)
    return polygon.area > 0

def draw_polygon(
    screen: pygame.Surface,
    polygon: shapely.Polygon,
    camera: Camera,
    color: Tuple[int,int,int],
    alpha: Optional[int] = None,
    world_coords: bool = True,
) -> bool:
    """Draw a shapely polygon on the screen."""
    if world_coords:
        screen_polygon = camera.world_to_screen_polygon(polygon, clip=True)
    else:
        screen_polygon = camera.get_screen_polygon().intersection(polygon)
    if not is_drawable(screen_polygon):
        return False
    if alpha is not None:
        min_x, min_y, max_x, max_y = screen_polygon.bounds
        surface = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)
        color = (*color, alpha)
    else:
        surface = screen
    if isinstance(screen_polygon, shapely.MultiPolygon):
        for polygon in screen_polygon:
            coords = polygon.exterior.coords[:-1]
            if alpha is not None:
                # Translate coordinates to surface space
                coords = [(x - min_x, y - min_y) for x, y in coords]
            pygame.gfxdraw.filled_polygon(surface, coords, color)
    else:
        coords = screen_polygon.exterior.coords[:-1]
        if alpha is not None:
            coords = [(x - min_x, y - min_y) for x, y in coords]
        pygame.gfxdraw.filled_polygon(surface, coords, color)
    if alpha is not None:
        screen.blit(surface, (min_x, min_y))
    return True

@contextmanager
def use_world(world_id: str) -> Generator[None, None, None]:
    """
    Context manager for temporarily switching to a different Esper world.
    
    Automatically switches back to the original world when exiting the context.
    """
    starting_world = esper.current_world
    esper.switch_world(world_id)
    try:
        yield
    finally:
        esper.switch_world(starting_world)

def get_unit_placements(team_type: TeamType, hex_coords: Tuple[int, int]) -> List[Tuple[UnitType, Tuple[int, int]]]:
    world_x, world_y = axial_to_world(*hex_coords)
    return [
        (unit_type.type, (round(pos.x - world_x), round(pos.y - world_y)))
        for ent, (unit_type, team, pos) in esper.get_components(UnitTypeComponent, Team, Position)
        if team.type == team_type and ent not in esper._dead_entities
    ]

def mouse_over_ui(manager: pygame_gui.UIManager) -> bool:
    return manager.get_hovering_any_element()

def has_unsaved_changes(battle: Battle) -> bool:
    """Check if current unit placements differ from saved solution.
    
    Args:
        hex_coords: The hex coordinates of the battle to check
        
    Returns:
        True if there are unsaved changes, False otherwise
    """
    with use_world(battle.id):
        saved_solution = progress_manager.solutions.get(battle.hex_coords)
        current_set = set(battle.allies) if battle.allies is not None else set()
        if saved_solution is None:
            return len(current_set) > 0
        saved_set = set(saved_solution.unit_placements)
        return current_set != saved_set
