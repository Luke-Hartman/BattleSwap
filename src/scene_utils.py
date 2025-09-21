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
from components.placing import Placing
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.unit_type import UnitType, UnitTypeComponent
from components.item import ItemComponent
from entities.items import ItemType
from game_constants import gc
from hex_grid import get_hex_vertices, axial_to_world
from components.team import Team, TeamType
from shapely.ops import nearest_points
from progress_manager import HexLifecycleState, progress_manager

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
        if esper.has_component(ent, Placing):
            continue
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
    mouse_pos: Tuple[int, int],
    battle_id: str,
    hex_coords: Tuple[int, int],
    camera: Camera,
    snap_to_grid: bool = False,
    required_team: Optional[TeamType] = None,
) -> Tuple[float, float]:
    world_pos = camera.screen_to_world(*mouse_pos)
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
    additional_unit_positions: Optional[List[Tuple[float, float]]] = None,
) -> shapely.Polygon:
    """Get the legal placement area for a hex.
    
    Args:
        battle_id: ID of the battle to check
        hex_coords: (q,r) axial coordinates of the hex
        required_team: If provided, restrict to this team's side
        include_units: If True, also restrict placement around existing units
        additional_unit_positions: Additional unit positions to consider as obstacles

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

    # Collect all unit positions (existing + additional)
    all_unit_positions = []
    
    # Get existing units if include_units is True
    if include_units:
        with use_world(battle_id):
            for ent, (pos, _) in esper.get_components(Position, UnitTypeComponent):
                if esper.has_component(ent, Placing):
                    continue
                all_unit_positions.append((pos.x, pos.y))
    
    # Add additional simulated positions
    if additional_unit_positions:
        all_unit_positions.extend(additional_unit_positions)
    
    # Remove circles around all units
    if all_unit_positions:
        legal_area = _get_legal_placement_area_helper(legal_area, tuple(all_unit_positions))
    
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

def get_unit_placements(team_type: TeamType, battle: Battle) -> List[Tuple[UnitType, Tuple[float, float], List[ItemType]]]:
    world_x, world_y = axial_to_world(*battle.hex_coords)
    with use_world(battle.id):
        return [
            (unit_type.type, (pos.x - world_x, pos.y - world_y), esper.component_for_entity(ent, ItemComponent).items)
            for ent, (unit_type, team, pos) in esper.get_components(UnitTypeComponent, Team, Position)
            if team.type == team_type and ent not in esper._dead_entities and not esper.has_component(ent, Placing)
        ]

def mouse_over_ui(manager: pygame_gui.UIManager) -> bool:
    return manager.get_hovering_any_element()

def has_unsaved_changes(battle: Battle, unit_placements: List[Tuple[UnitType, Tuple[float, float], List[ItemType]]]) -> bool:
    """Check if current unit placements differ from saved solution.
    
    Args:
        battle: The battle to check
        unit_placements: Current unit placements
        
    Returns:
        True if there are unsaved changes, False otherwise
    """
    saved_solution = progress_manager.solutions.get(battle.hex_coords)
    # Convert items lists to tuples for hashing
    current_set = set((unit_type, position, tuple(items)) for unit_type, position, items in unit_placements)
    
    if saved_solution is None:
        return len(current_set) > 0
    
    # Check if the corruption state matches
    current_is_corrupted = progress_manager.get_hex_state(battle.hex_coords) in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]
    if saved_solution.solved_corrupted != current_is_corrupted:
        return True
        
    # Convert saved solution items lists to tuples for hashing
    saved_set = set((unit_type, position, tuple(items)) for unit_type, position, items in saved_solution.unit_placements)
    return current_set != saved_set

def calculate_group_placement_positions(
    mouse_world_pos: Tuple[float, float],
    unit_offsets: List[Tuple[float, float]],
    battle_id: str,
    hex_coords: Tuple[int, int],
    required_team: Optional[TeamType] = None,
    snap_to_grid: bool = False,
    sandbox_mode: bool = False,
) -> List[Tuple[float, float]]:
    """Calculate placement positions for a group of units.
    
    This function ensures that:
    1. Each unit ends up on a different grid cell (when grid snapping is enabled)
    2. All units are on the legal side for the correct team
    3. No units end up outside the legal zone
    4. Units don't overlap with existing units
    
    Args:
        mouse_world_pos: World position of the mouse cursor
        unit_offsets: List of (x, y) offsets from the group center for each unit
        battle_id: ID of the battle
        hex_coords: Hex coordinates of the battle
        required_team: Team restriction (if any)
        snap_to_grid: Whether to snap to grid
        sandbox_mode: Whether in sandbox mode
        
    Returns:
        List of (x, y) world positions for each unit
    """
    if not unit_offsets:
        return []
    
    # Calculate positions sequentially, each considering previously placed units
    calculated_positions = []
    
    for i, (offset_x, offset_y) in enumerate(unit_offsets):
        # Calculate ideal position
        ideal_x = mouse_world_pos[0] + offset_x
        ideal_y = mouse_world_pos[1] + offset_y
        
        # Get legal area considering existing units + previously calculated positions
        legal_area = get_legal_placement_area(
            battle_id,
            hex_coords,
            required_team=required_team,
            additional_unit_positions=calculated_positions,
        )
        
        # Clip to legal placement area
        clipped_pos = clip_to_polygon(legal_area, ideal_x, ideal_y)
        
        # Apply grid snapping if enabled
        if snap_to_grid:
            clipped_pos = snap_position_to_grid(clipped_pos[0], clipped_pos[1], hex_coords)
            
            # If grid snapping results in collision, try nearby grid positions
            if calculated_positions:
                # Check if this grid position would collide with any previously placed units
                min_distance = gc.UNIT_PLACEMENT_MINIMUM_DISTANCE
                for prev_pos in calculated_positions:
                    distance = ((clipped_pos[0] - prev_pos[0])**2 + (clipped_pos[1] - prev_pos[1])**2)**0.5
                    if distance < min_distance:
                        # Find nearest available grid position
                        clipped_pos = find_nearest_available_grid_position(
                            clipped_pos[0], clipped_pos[1], hex_coords, legal_area, calculated_positions
                        )
                        break
        
        calculated_positions.append(clipped_pos)
    
    return calculated_positions

def find_nearest_available_grid_position(
    x: float, 
    y: float, 
    hex_coords: Tuple[int, int], 
    legal_area: shapely.Polygon, 
    occupied_positions: List[Tuple[float, float]]
) -> Tuple[float, float]:
    """Find the nearest available grid position that doesn't collide with occupied positions.
    
    Args:
        x: Initial x coordinate
        y: Initial y coordinate
        hex_coords: Hex coordinates for grid reference
        legal_area: Legal placement area
        occupied_positions: List of already occupied positions
        
    Returns:
        Tuple of (x, y) coordinates for the nearest available grid position
    """
    # Start from the given position
    center_x, center_y = axial_to_world(*hex_coords)
    
    # Convert to grid coordinates
    grid_x = round((x - center_x) / gc.GRID_SIZE)
    grid_y = round((y - center_y) / gc.GRID_SIZE)
    
    # Try positions in expanding spiral pattern
    for radius in range(0, 20):  # Maximum search radius
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) != radius and abs(dy) != radius and radius > 0:
                    continue  # Only check perimeter of current radius
                
                test_grid_x = grid_x + dx
                test_grid_y = grid_y + dy
                
                # Convert back to world coordinates
                test_x = test_grid_x * gc.GRID_SIZE + center_x
                test_y = test_grid_y * gc.GRID_SIZE + center_y
                
                # Check if position is in legal area
                test_point = shapely.Point(test_x, test_y)
                if not legal_area.contains(test_point):
                    continue
                
                # Check if position is far enough from occupied positions
                min_distance = gc.UNIT_PLACEMENT_MINIMUM_DISTANCE
                is_valid = True
                for occupied_pos in occupied_positions:
                    distance = ((test_x - occupied_pos[0])**2 + (test_y - occupied_pos[1])**2)**0.5
                    if distance < min_distance:
                        is_valid = False
                        break
                
                if is_valid:
                    return (test_x, test_y)
    
    # If no grid position found, return the clipped position
    return clip_to_polygon(legal_area, x, y)
