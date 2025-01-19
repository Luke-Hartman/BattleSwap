from enum import Enum, auto
import enum
from typing import Dict, List, Optional, Tuple
import esper
import pygame
import pygame_gui
from shapely import Polygon

from game_constants import gc, reload_game_constants
from auto_battle import AutoBattle
from battles import Battle
from components.position import Position
from components.team import Team, TeamType
from components.unit_type import UnitType, UnitTypeComponent
from entities.units import create_unit
from processors.animation_processor import AnimationProcessor
from processors.orientation_processor import OrientationProcessor
from processors.position_processor import PositionProcessor
from processors.rendering_processor import RenderingProcessor
from processors.rotation_processor import RotationProcessor
from camera import Camera
from hex_grid import (
    axial_to_world,
    world_to_axial,
    get_hex_vertices,
    get_hex_bounds,
    get_edge_vertices,
    get_edges_for_hexes
)
from processors.targetting_processor import TargettingProcessor
from processors.transparency_processor import TransparencyProcessor
from scene_utils import draw_polygon, use_world, get_hovered_unit
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from time_manager import time_manager
from components.focus import Focus
from selected_unit_manager import selected_unit_manager


class FillState(Enum):
    """State determining how a hex should be filled."""
    NORMAL = auto()
    HIGHLIGHTED = auto()
    UNFOCUSED = auto()
    FOGGED = auto()

class BorderState(Enum):
    """State determining how a hex border should be drawn."""
    NORMAL = auto()
    GREEN_BORDER = auto()
    YELLOW_BORDER = auto()

class HexState:
    """Combined state for both fill and border of a hex."""
    def __init__(self, fill: FillState = FillState.NORMAL, border: BorderState = BorderState.NORMAL):
        self.fill = fill
        self.border = border

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HexState):
            return NotImplemented
        return self.fill == other.fill and self.border == other.border

class WorldMapView:
    # Configuration constants

    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        battles: List[Battle],
        camera: Camera
    ) -> None:
        """
        Initialize the world map view.

        :param screen: The main pygame display surface.
        :param manager: The pygame_gui UI manager.
        :param battles: A list of Battle objects with defined hex_coords.
        :param camera: A Camera instance for world-to-screen transformations.
        """
        self.screen = screen
        self.manager = manager
        self.camera = camera
        self.default_world = "__default__"

        self.hex_states: Dict[Tuple[int, int], HexState] = {}
        self.rebuild(battles, cleanup=False)
    
    def _initialize_battle_world(self, battle: Battle) -> None:
        if battle.id in esper.list_worlds():
            esper.delete_world(battle.id)
        with use_world(battle.id):
            esper.add_processor(TransparencyProcessor())
            esper.add_processor(RenderingProcessor(self.screen, self.camera, self.manager))
            esper.add_processor(AnimationProcessor())
            esper.add_processor(PositionProcessor())
            esper.add_processor(OrientationProcessor())
            esper.add_processor(RotationProcessor())
            esper.add_processor(TargettingProcessor())
            world_x, world_y = axial_to_world(*battle.hex_coords)
            for unit_type, position in battle.allies or []:
                create_unit(
                    position[0] + world_x,
                    position[1] + world_y,
                    unit_type,
                    TeamType.TEAM1
                )
            for unit_type, position in battle.enemies:
                create_unit(
                    position[0] + world_x,
                    position[1] + world_y,
                    unit_type,
                    TeamType.TEAM2
                )

    def get_battle_from_hex(self, hex_coords: Tuple[int, int]) -> Optional[Battle]:
        return next((battle for battle in self.battles.values() if battle.hex_coords == hex_coords), None)

    def focus_hovered_unit(self) -> None:
        """Focus the unit under the mouse cursor."""
        if not self.manager.get_hovering_any_element():
            battle = self.get_battle_from_hex(self.get_hex_at_mouse_pos())
            if battle is None:
                return
            with use_world(battle.id):
                hovered_unit = get_hovered_unit(self.camera)
                if hovered_unit is not None:
                    esper.add_component(hovered_unit, Focus())
                    unit_type = esper.component_for_entity(hovered_unit, UnitTypeComponent).type
                    selected_unit_manager.selected_unit_type = unit_type
                else:
                    selected_unit_manager.selected_unit_type = None

    # ------------------------------
    # Public API
    # ------------------------------

    def move_camera_above_battle(self, battle_id: str) -> None:
        """Move the camera above the specified battle."""
        battle = self.battles[battle_id]
        assert battle.hex_coords is not None
        x, y = axial_to_world(*battle.hex_coords)
        self.camera.move(x, y, zoom=1/2)

    def draw_map(self) -> None:
        """Draw all visible battle hexes and edges."""
        self._draw_hexes()
        self._draw_visible_edges()

    def update_battles(self, time_delta: float) -> None:
        """
        Update and render the battles. Call after draw_map.
        
        Only processes battles that are not in a fogged state.
        """
        self.focus_hovered_unit()
        
        for battle in self.battles.values():
            # Don't draw/update units for fogged battles
            if self.hex_states.get(battle.hex_coords, HexState()).fill == FillState.FOGGED:
                continue
            
            esper.switch_world(battle.id)
            # dt should be either 1/60 or 0. This makes sure the game is deterministic.
            esper.process(time_manager.dt)

    def get_hex_states(self) -> Dict[Tuple[int, int], HexState]:
        """Return a copy of all current hex states."""
        return self.hex_states.copy()

    def update_hex_state(self, states: Dict[Tuple[int, int], HexState]) -> None:
        """Update the state of multiple hexes at once."""
        self.hex_states.update(states)

    def reset_hex_states(self) -> None:
        """Reset the state of all hexes to normal."""
        self.hex_states = {
            battle.hex_coords: HexState()
            for battle in self.battles.values()
        }
    
    def add_unit(self, battle_id: str, unit_type: UnitType, position: Tuple[int, int], team: TeamType) -> None:
        """
        Add a unit to the specified battle and play a sound effect.

        Args:
            battle_id: ID of the battle to add the unit to
            unit_type: Type of unit to create
            position: Position to place the unit at
            team: Team the unit belongs to
        """
        esper.switch_world(battle_id)
        world_x, world_y = axial_to_world(*self.battles[battle_id].hex_coords)
        create_unit(
            position[0],
            position[1],
            unit_type,
            team
        )
        if team == TeamType.TEAM1:
            if self.battles[battle_id].allies is None:
                self.battles[battle_id].allies = []
            self.battles[battle_id].allies.append((unit_type, (position[0] - world_x, position[1] - world_y)))
        else:
            self.battles[battle_id].enemies.append((unit_type, (position[0] - world_x, position[1] - world_y)))
        emit_event(PLAY_SOUND, event=PlaySoundEvent(
            filename="unit_placed.wav",
            volume=0.5
        ))
    
    def remove_unit(self, battle_id: str, unit_id: int, required_team: Optional[TeamType] = None) -> bool:
        """
        Remove a unit from the specified battle and play a sound effect.
        
        Args:
            battle_id: ID of the battle to remove the unit from
            unit_id: Entity ID of the unit to remove
            required_team: If provided, only remove units of this team
            
        Returns:
            True if the unit was removed, False if it wasn't (wrong team)
        """
        esper.switch_world(battle_id)
        team = esper.component_for_entity(unit_id, Team)
        if required_team is not None:
            if team.type != required_team:
                return False
        position = esper.component_for_entity(unit_id, Position)
        world_x, world_y = axial_to_world(*self.battles[battle_id].hex_coords)
        local_x, local_y = position.x - world_x, position.y - world_y
        if team.type == TeamType.TEAM1:
            found_unit = next((unit for unit in self.battles[battle_id].allies if unit[1] == (local_x, local_y)), None)
            if found_unit is None:
                raise ValueError(f"Unit {unit_id} not found in allies by position")
            self.battles[battle_id].allies.remove(found_unit)
        else:
            found_unit = next((unit for unit in self.battles[battle_id].enemies if unit[1] == (local_x, local_y)), None)
            if found_unit is None:
                raise ValueError(f"Unit {unit_id} not found in enemies by position")
            self.battles[battle_id].enemies.remove(found_unit)

        esper.delete_entity(unit_id)
        emit_event(PLAY_SOUND, event=PlaySoundEvent(
            filename="unit_returned.wav",
            volume=0.5
        ))
        return True

    def _cleanup(self) -> None:
        esper.switch_world(self.default_world)
        for battle in self.battles.values():
            if battle.id in esper.list_worlds():
                esper.delete_world(battle.id)

    def __del__(self) -> None:
        self._cleanup()

    def rebuild(self, battles: List[Battle], cleanup: bool = True) -> None:
        """
        Rebuild the world map view with new battles while preserving camera state.
        
        Args:
            battles: A list of Battle objects with defined hex_coords.
            cleanup: Whether to clean up existing battle worlds.
        """
        if cleanup:
            self._cleanup()

        self.battles = {
            battle.id: battle.model_copy(deep=True)
            for battle in battles
            if battle.hex_coords is not None
        }
        
        self.reset_hex_states()
        reload_game_constants()

        for battle in self.battles.values():
            self._initialize_battle_world(battle)
        
        self.hovered_hex: Optional[Tuple[int, int]] = None
        self.selected_hex: Optional[Tuple[int, int]] = None

    # ------------------------------
    # Drawing Helpers
    # ------------------------------

    def _draw_hexes(self) -> None:
        """Draw the fills and overlays of all hexes currently visible."""
        for coords in self.hex_states.keys():
            if not self._is_hex_off_screen(coords):
                state = self.hex_states[coords]
                self._draw_single_hex(coords, state)


    def _draw_single_hex(
        self,
        coords: Tuple[int,int],
        state: HexState
    ) -> None:
        """Draw a single hex cell with the appropriate fill and overlay."""
        vertices = get_hex_vertices(*coords)
        screen_polygon = self.camera.world_to_screen_polygon(
            Polygon(vertices)
        )
        if screen_polygon.area == 0:
            # Hex is completely off screen
            return

        # Draw base hex fill
        if self.get_battle_from_hex(coords) is not None:
            draw_polygon(
                screen=self.screen, 
                polygon=screen_polygon, 
                camera=self.camera, 
                color=gc.MAP_BATTLEFIELD_COLOR, 
                alpha=None,
                world_coords=False,
            )

        # Draw fill overlay based on state
        if state.fill == FillState.HIGHLIGHTED:
            draw_polygon(
                screen=self.screen, 
                polygon=screen_polygon, 
                camera=self.camera, 
                color=gc.MAP_HIGHLIGHT_COLOR[:3], 
                alpha=gc.MAP_HIGHLIGHT_COLOR[3],
                world_coords=False,
            )
        elif state.fill == FillState.FOGGED:
            draw_polygon(
                screen=self.screen, 
                polygon=screen_polygon, 
                camera=self.camera, 
                color=gc.MAP_FOG_COLOR[:3], 
                alpha=gc.MAP_FOG_COLOR[3],
                world_coords=False,
            )
        elif state.fill == FillState.UNFOCUSED:
            draw_polygon(
                screen=self.screen, 
                polygon=screen_polygon, 
                camera=self.camera, 
                color=gc.MAP_UNFOCUSED_COLOR[:3], 
                alpha=gc.MAP_UNFOCUSED_COLOR[3],
                world_coords=False,
            )


    def _draw_visible_edges(self) -> None:
        """Draw edges between adjacent hexes."""
        on_screen_hexes = set(
            coords
            for coords in self.hex_states.keys()
            if not self._is_hex_off_screen(coords)
        )
        edges = get_edges_for_hexes(on_screen_hexes)
        for edge in edges:
            self._draw_edge(edge)

    def _draw_edge(self, edge: frozenset[Tuple[int,int]]) -> None:
        """Draw a single edge (line) between two adjacent hexes."""
        is_battle_edge = any(
            self.get_battle_from_hex(coords) is not None
            for coords in edge
        )
        
        # Get the most prominent border state of the two hexes
        border_states = [self.hex_states.get(coords, HexState()).border for coords in edge]
        if BorderState.YELLOW_BORDER in border_states:
            color = (255, 255, 0)
            width = 2
        elif BorderState.GREEN_BORDER in border_states:
            color = (0, 255, 0)
            width = 2
        elif is_battle_edge:
            color = gc.MAP_BATTLEFIELD_EDGE_COLOR
            width = 3
        else:
            return

        v1, v2 = get_edge_vertices(edge)
        screen_v1 = self.camera.world_to_screen(*v1)
        screen_v2 = self.camera.world_to_screen(*v2)
        pygame.draw.line(self.screen, color, screen_v1, screen_v2, width=width)

    # ------------------------------
    # Geometry & Visibility Helpers
    # ------------------------------

    def _is_hex_off_screen(self, coords: Tuple[int, int]) -> bool:
        """
        Check if a hex is completely off screen.

        Args:
            coords: Axial coordinates (q, r)

        Returns:
            True if the hex is completely off screen, False if any part is visible
        """
        return self.camera.is_box_off_screen(*get_hex_bounds(*coords))

    def get_hex_at_mouse_pos(self) -> Optional[Tuple[int, int]]:
        """
        Get the hex coordinates at the current mouse position.

        Returns:
            Axial coordinates of the hex if it contains a battle, else None
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
        hex_coords = world_to_axial(world_x, world_y)
        return hex_coords
