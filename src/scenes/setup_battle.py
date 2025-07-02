"""Sandbox scene for experimenting with unit placement and battles."""
from typing import Optional, Tuple, List
import esper
import pygame
import pygame_gui
import shapely
import battles
from components.focus import Focus
from components.placing import Placing
from components.position import Position
from components.team import Team, TeamType
from components.transparent import Transparency
from components.unit_type import UnitType, UnitTypeComponent
from entities.units import create_unit
from events import CHANGE_MUSIC, PLAY_SOUND, ChangeMusicEvent, PlaySoundEvent, emit_event, UNMUTE_DRUMS, UnmuteDrumsEvent
from hex_grid import axial_to_world
from progress_manager import progress_manager
from scenes.scene import Scene
from game_constants import gc
from camera import Camera
from ui_components.barracks_ui import BarracksUI
from ui_components.corruption_icon import CorruptionIcon
from ui_components.feedback_button import FeedbackButton
from ui_components.return_button import ReturnButton
from ui_components.start_button import StartButton
from scenes.events import BattleSceneEvent, PreviousSceneEvent
from ui_components.save_battle_dialog import SaveBattleDialog
from auto_battle import BattleOutcome, simulate_battle
from ui_components.tip_box import TipBox
from voice import play_intro
from world_map_view import FillState, HexState, WorldMapView
from scene_utils import draw_grid, get_center_line, get_placement_pos, get_hovered_unit, get_unit_placements, get_legal_placement_area, clip_to_polygon, has_unsaved_changes, mouse_over_ui, snap_position_to_grid
from ui_components.progress_panel import ProgressPanel
from ui_components.corruption_power_editor import CorruptionPowerEditorDialog
from corruption_powers import CorruptionPower
from selected_unit_manager import selected_unit_manager
from components.sprite_sheet import SpriteSheet


class SetupBattleScene(Scene):
    """A scene for setting up a battle.

    Has additional options for sandbox and developer modes.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        world_map_view: Optional[WorldMapView],
        battle_id: Optional[str],
        sandbox_mode: bool = False,
        developer_mode: bool = False,
    ):
        """Initialize the sandbox scene.
        
        Args:
            screen: The pygame surface to render to.
            manager: The pygame_gui manager for the scene.
            world_map_view: The world map view for the scene.
            battle_id: Which battle is focused.
            sandbox_mode: In sandbox mode, there are no restrictions on unit placement.
            developer_mode: In developer mode, there are additional buttons such as saving
                and simulating the battle.
        """
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        emit_event(UNMUTE_DRUMS, event=UnmuteDrumsEvent())
        self.screen = screen
        self.manager = manager
        self.world_map_view = world_map_view
        self.camera = world_map_view.camera
        self.battle_id = battle_id
        self.battle = world_map_view.battles[battle_id]
        self.sandbox_mode = sandbox_mode
        self.developer_mode = developer_mode
        
        # Drag selection state
        self.is_drag_selecting = False
        self.drag_start_pos: Optional[Tuple[int, int]] = None
        self.drag_end_pos: Optional[Tuple[int, int]] = None
        
        # Multi-unit pickup state (like single unit pickup but for groups)
        self.selected_group_partial_units: List[int] = []  # List of partial unit entity IDs
        self.group_unit_offsets: List[Tuple[float, float]] = []  # Relative offsets from mouse
        self.group_unit_types: List[UnitType] = []  # Unit types for each partial unit
        self.group_placement_team: Optional[TeamType] = None  # Team for the group
        
        if self.sandbox_mode:
            # Set unfocused states for all battles except the focused one
            unfocused_states = {
                other_battle.hex_coords: HexState(fill=FillState.UNFOCUSED) if other_battle.hex_coords != self.battle.hex_coords else HexState(fill=FillState.NORMAL)
                for other_battle in self.world_map_view.battles.values()
            }
        else:
            # Set unfocused for all solved battles except the focused one
            # Set fogged for all unsolved battles
            unfocused_states = {}
            for other_battle in self.world_map_view.battles.values():
                if other_battle.hex_coords == self.battle.hex_coords:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.NORMAL)
                else:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.FOGGED)
        self.world_map_view.reset_hex_states()
        self.world_map_view.update_hex_state(unfocused_states)

        self.return_button = ReturnButton(self.manager)
        self.start_button = StartButton(self.manager)
        self.feedback_button = FeedbackButton(self.manager)
        self.tip_box = TipBox(self.manager, self.battle)
        
        if self.battle.hex_coords in self.world_map_view.corrupted_hexes:
            icon_size = (48, 48)
            icon_position = (pygame.display.Info().current_w - icon_size[0] - 15, 50)
            self.corruption_icon = CorruptionIcon(
                manager=self.manager,
                position=icon_position,
                size=icon_size,
                battle_hex_coords=self.battle.hex_coords,
                corruption_powers=self.battle.corruption_powers
            )
        else:
            self.corruption_icon = None

        self.barracks = BarracksUI(
            self.manager,
            starting_units={} if self.sandbox_mode else progress_manager.available_units(self.battle),
            interactive=True,
            sandbox_mode=self.sandbox_mode,
            current_battle=self.battle,
        )

        # Add clear button above the barracks
        barracks_x = self.barracks.rect.x
        self.clear_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (barracks_x, self.barracks.rect.y - 40),
                (100, 30)
            ),
            text='Clear All',
            manager=self.manager
        )

        # Create grades panel to the right of barracks, aligned at the bottom
        barracks_bottom = self.barracks.rect.bottom
        self.progress_panel = ProgressPanel(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 295, barracks_bottom - 100),
                (215, 100)
            ),
            manager=self.manager,
            current_battle=self.battle,
            is_setup_mode=not self.battle.is_test,  # Only use setup mode for non-test battles
        ) if not self.sandbox_mode else None

        self.save_dialog: Optional[SaveBattleDialog] = None
        if self.developer_mode:
            self.save_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 310, 10),
                    (100, 30)
                ),
                text='Save Battle',
                manager=self.manager
            )
            self.simulate_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 420, 10),
                    (100, 30)
                ),
                text='Simulate',
                manager=self.manager
            )
            self.results_box = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 420, 50),  # Position below simulate button
                    (100, 30)
                ),
                text='',
                manager=self.manager
            )
            # Add edit corruption powers button
            self.edit_corruption_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 530, 10),
                    (100, 30)
                ),
                text='Edit Powers',
                manager=self.manager
            )
            # Add toggle corruption button
            self.toggle_corruption_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 530, 50),
                    (100, 30)
                ),
                text='Toggle Corruption',
                manager=self.manager
            )
        else:
            self.save_button = None
            self.simulate_button = None
            self.results_box = None
            self.edit_corruption_button = None
            self.toggle_corruption_button = None
        
        self.confirmation_dialog: Optional[pygame_gui.windows.UIConfirmationDialog] = None
    
    def calculate_group_positions(
        self,
        mouse_world_pos: Tuple[float, float],
        unit_offsets: List[Tuple[float, float]], 
        battle_hex_coords: Tuple[int, int],
        snap_to_grid: bool,
        required_team: Optional[TeamType],
        current_unit_positions: Optional[List[Tuple[float, float]]] = None,
    ) -> List[Tuple[float, float]]:
        """Calculate final positions for a group of units, handling grid snapping and collision avoidance.
        
        This is the unified logic for both preview and actual placement.
        
        Args:
            mouse_world_pos: Mouse position in world coordinates
            unit_offsets: List of (x, y) offsets from mouse for each unit
            battle_hex_coords: Hex coordinates of the battle
            snap_to_grid: Whether to snap positions to grid
            required_team: Required team for placement (None in sandbox mode)
            current_unit_positions: Existing unit positions to avoid (for preview calculation)
            
        Returns:
            List of calculated (x, y) positions for each unit
        """
        calculated_positions = []
        occupied_grid_cells = set()  # Track occupied grid cells when snapping
        
        # Include current unit positions if provided
        if current_unit_positions:
            for pos in current_unit_positions:
                if snap_to_grid:
                    # Track the grid cell as occupied
                    snapped = snap_position_to_grid(pos[0], pos[1], battle_hex_coords)
                    occupied_grid_cells.add(snapped)
        
        for i, (offset_x, offset_y) in enumerate(unit_offsets):
            ideal_x = mouse_world_pos[0] + offset_x
            ideal_y = mouse_world_pos[1] + offset_y
            
            # Get legal area considering existing units + previously calculated positions in this group
            legal_area = get_legal_placement_area(
                self.battle_id,
                battle_hex_coords,
                required_team=required_team,
                additional_unit_positions=calculated_positions,
            )
            
            # Clip to legal placement area first
            clipped_x, clipped_y = clip_to_polygon(legal_area, ideal_x, ideal_y)
            
            if snap_to_grid:
                # Snap to grid
                snapped_x, snapped_y = snap_position_to_grid(clipped_x, clipped_y, battle_hex_coords)
                
                # Check if this grid cell is already occupied
                if (snapped_x, snapped_y) in occupied_grid_cells:
                    # Find the nearest unoccupied grid cell
                    best_pos = self._find_nearest_free_grid_cell(
                        clipped_x, clipped_y,
                        battle_hex_coords,
                        occupied_grid_cells,
                        legal_area,
                        required_team
                    )
                    if best_pos:
                        snapped_x, snapped_y = best_pos
                    # If no free grid cell found, keep the original snapped position
                    # (this shouldn't happen in practice with proper spacing)
                
                occupied_grid_cells.add((snapped_x, snapped_y))
                final_pos = (snapped_x, snapped_y)
            else:
                final_pos = (clipped_x, clipped_y)
            
            calculated_positions.append(final_pos)
        
        return calculated_positions
    
    def _find_nearest_free_grid_cell(
        self,
        x: float, 
        y: float,
        battle_hex_coords: Tuple[int, int],
        occupied_cells: set[Tuple[float, float]],
        legal_area: shapely.Polygon,
        required_team: Optional[TeamType]
    ) -> Optional[Tuple[float, float]]:
        """Find the nearest unoccupied grid cell to the given position.
        
        Args:
            x, y: Starting position
            battle_hex_coords: Hex coordinates for grid alignment
            occupied_cells: Set of already occupied grid positions
            legal_area: Legal placement area polygon
            required_team: Required team for placement
            
        Returns:
            Tuple of (x, y) for nearest free grid cell, or None if none found
        """
        # Search in expanding rings
        max_search_distance = 10  # Maximum grid cells to search
        
        for distance in range(1, max_search_distance + 1):
            # Check all grid positions at this distance
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    # Only check positions at exactly this distance (ring pattern)
                    if max(abs(dx), abs(dy)) != distance:
                        continue
                    
                    test_x = x + dx * gc.GRID_SIZE
                    test_y = y + dy * gc.GRID_SIZE
                    
                    # Snap to grid
                    snapped_x, snapped_y = snap_position_to_grid(test_x, test_y, battle_hex_coords)
                    
                    # Check if this grid cell is free and in legal area
                    if (snapped_x, snapped_y) not in occupied_cells:
                        # Verify it's in the legal area
                        if legal_area.contains(shapely.Point(snapped_x, snapped_y)):
                            return (snapped_x, snapped_y)
        
        return None

    def show_exit_confirmation(self) -> None:
        """Show confirmation dialog for exiting with unsaved changes."""
        self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect((pygame.display.Info().current_w/2 - 150, pygame.display.Info().current_h/2 - 100), (300, 200)),
            manager=self.manager,
            window_title="Unsaved Changes",
            action_long_desc="You have unsaved changes. Are you sure you want to exit?" if not self.sandbox_mode else "Are you sure you want to exit?",
            action_short_name="Exit",
            blocking=True
        )

    def handle_return(self) -> None:
        """Handle return button press or escape key."""
        if (
            not self.sandbox_mode and has_unsaved_changes(self.battle)
            or self.sandbox_mode and (
                len(get_unit_placements(TeamType.TEAM1, self.battle)) > 0
                or len(get_unit_placements(TeamType.TEAM2, self.battle)) > 0
            )
        ):
            self.show_exit_confirmation()
        else:
            self.world_map_view.move_camera_above_battle(self.battle_id)
            self.world_map_view.rebuild(battles=progress_manager.get_battles_including_solutions())
            pygame.event.post(PreviousSceneEvent().to_event())

    def pickup_group_of_units(self, unit_ids: List[int], mouse_world_pos: Tuple[float, float], placement_team: TeamType) -> None:
        """Pick up a group of units as transparent previews, like single unit pickup."""
        if not unit_ids:
            return
            
        esper.switch_world(self.battle_id)
        
        # Clear any existing group pickup
        self.clear_group_pickup()
        
        # Calculate center of selected units for centering on mouse
        center_x = sum(esper.component_for_entity(uid, Position).x for uid in unit_ids) / len(unit_ids)
        center_y = sum(esper.component_for_entity(uid, Position).y for uid in unit_ids) / len(unit_ids)
        
        # Store data for each unit and create partial units
        for unit_id in unit_ids:
            if not esper.entity_exists(unit_id):
                continue
                
            pos = esper.component_for_entity(unit_id, Position)
            unit_type_comp = esper.component_for_entity(unit_id, UnitTypeComponent)
            
            # Calculate offset from group center
            offset_x = pos.x - center_x
            offset_y = pos.y - center_y
            self.group_unit_offsets.append((offset_x, offset_y))
            self.group_unit_types.append(unit_type_comp.type)
            
            # Create transparent partial unit
            partial_unit = create_unit(
                x=mouse_world_pos[0] + offset_x,
                y=mouse_world_pos[1] + offset_y,
                unit_type=unit_type_comp.type,
                team=placement_team,
                corruption_powers=self.battle.corruption_powers
            )
            esper.add_component(partial_unit, Placing())
            esper.add_component(partial_unit, Transparency(alpha=128))
            self.selected_group_partial_units.append(partial_unit)
            
            # Remove original unit from battlefield (but don't add to barracks since we're carrying them)
            self.world_map_view.remove_unit(self.battle_id, unit_id)
        
        self.group_placement_team = placement_team

    def clear_group_pickup(self) -> None:
        """Clear the group pickup state and delete partial units."""
        esper.switch_world(self.battle_id)
        
        # Delete all partial units
        for partial_unit in self.selected_group_partial_units:
            if esper.entity_exists(partial_unit):
                esper.delete_entity(partial_unit)
        
        # Clear state
        self.selected_group_partial_units.clear()
        self.group_unit_offsets.clear()
        self.group_unit_types.clear()
        self.group_placement_team = None

    def place_group_units(self, mouse_world_pos: Tuple[float, float], snap_to_grid: bool = False) -> None:
        """Place all units from the group pickup."""
        if not self.selected_group_partial_units or self.group_placement_team is None:
            return
            
        esper.switch_world(self.battle_id)
        
        # Calculate positions using the shared logic
        calculated_positions = self.calculate_group_positions(
            mouse_world_pos=mouse_world_pos,
            unit_offsets=self.group_unit_offsets,
            battle_hex_coords=self.battle.hex_coords,
            snap_to_grid=snap_to_grid,
            required_team=None if self.sandbox_mode else TeamType.TEAM1,
            current_unit_positions=None,  # Don't need to consider existing units for placement
        )
        
        # Place each unit at calculated position
        for i, (unit_type, position) in enumerate(zip(self.group_unit_types, calculated_positions)):
            # Create the unit
            self.world_map_view.add_unit(
                self.battle_id,
                unit_type,
                position,
                self.group_placement_team,
            )
        
        # Clear the group pickup
        self.clear_group_pickup()
        
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)

    def cancel_group_pickup(self) -> None:
        """Cancel group pickup and return units to barracks."""
        if not self.selected_group_partial_units:
            return
            
        # Return units to barracks inventory
        for unit_type in self.group_unit_types:
            self.barracks.add_unit(unit_type)
        
        # Clear the group pickup
        self.clear_group_pickup()
        
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)

    def clear_allied_units(self) -> None:
        """Remove all allied units from the battlefield."""
        # Get all allied units in the current world
        esper.switch_world(self.battle_id)
        allied_units = []
        for ent, (team, unit_type) in esper.get_components(Team, UnitTypeComponent):
            if team.type == TeamType.TEAM1 and not esper.has_component(ent, Placing):
                allied_units.append((ent, unit_type.type))
        
        # Remove each allied unit and return to barracks
        for unit_id, unit_type in allied_units:
            if esper.entity_exists(unit_id):  # Check if entity still exists before removing
                self.world_map_view.remove_unit(self.battle_id, unit_id)
                self.barracks.add_unit(unit_type)
        
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)

    def sprite_intersects_rect(self, sprite: SpriteSheet, min_x: float, max_x: float, min_y: float, max_y: float) -> bool:
        """Check if any non-transparent pixels of a sprite intersect with the given rectangle."""
        # First do a quick bounding box check
        if not (sprite.rect.left <= max_x and sprite.rect.right >= min_x and 
                sprite.rect.top <= max_y and sprite.rect.bottom >= min_y):
            return False
        
        # Calculate the intersection area between sprite and selection rectangle
        intersect_left = max(sprite.rect.left, min_x)
        intersect_right = min(sprite.rect.right, max_x)
        intersect_top = max(sprite.rect.top, min_y)
        intersect_bottom = min(sprite.rect.bottom, max_y)
        
        # Convert world coordinates to sprite-local coordinates
        sprite_start_x = int(intersect_left - sprite.rect.left)
        sprite_end_x = int(intersect_right - sprite.rect.left)
        sprite_start_y = int(intersect_top - sprite.rect.top)
        sprite_end_y = int(intersect_bottom - sprite.rect.top)
        
        # Clamp to sprite bounds
        sprite_start_x = max(0, min(sprite_start_x, sprite.rect.width))
        sprite_end_x = max(0, min(sprite_end_x, sprite.rect.width))
        sprite_start_y = max(0, min(sprite_start_y, sprite.rect.height))
        sprite_end_y = max(0, min(sprite_end_y, sprite.rect.height))
        
        # Check if any non-transparent pixels exist in the intersection area
        for x in range(sprite_start_x, sprite_end_x):
            for y in range(sprite_start_y, sprite_end_y):
                try:
                    if sprite.image.get_at((x, y)).a != 0:  # Non-transparent pixel
                        return True
                except IndexError:
                    continue
        
        return False

    def select_units_in_rect(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> None:
        """Select all units within the given screen rectangle and pick them up."""
        esper.switch_world(self.battle_id)
        
        # Convert screen coordinates to world coordinates
        start_world = self.camera.screen_to_world(*start_pos)
        end_world = self.camera.screen_to_world(*end_pos)
        
        # Create selection rectangle in world coordinates
        min_x = min(start_world[0], end_world[0])
        max_x = max(start_world[0], end_world[0])
        min_y = min(start_world[1], end_world[1])
        max_y = max(start_world[1], end_world[1])
        
        # Ensure minimum size for single clicks
        max_x = max(max_x, min_x + 1)
        max_y = max(max_y, min_y + 1)
        
        # Find units within the rectangle
        selected_units = []
        placement_team = None
        
        for ent, (pos, unit_type, team) in esper.get_components(Position, UnitTypeComponent, Team):
            if esper.has_component(ent, Placing):
                continue
            
            # Get sprite component for intersection checking
            if not esper.has_component(ent, SpriteSheet):
                continue
            sprite = esper.component_for_entity(ent, SpriteSheet)
            
            # Check if sprite (considering transparency) intersects with selection rectangle
            if self.sprite_intersects_rect(sprite, min_x, max_x, min_y, max_y):
                # Only select units that can be moved (team1 units or all units in sandbox mode)
                if self.sandbox_mode or team.type == TeamType.TEAM1:
                    selected_units.append(ent)
                    if placement_team is None:
                        # Determine placement team from first selected unit
                        world_x, _ = axial_to_world(*self.battle.hex_coords)
                        placement_team = TeamType.TEAM1 if pos.x < world_x else TeamType.TEAM2
        
        # If units were selected, pick them up
        if selected_units and placement_team is not None:
            # Calculate mouse world position for centering
            mouse_pos = pygame.mouse.get_pos()
            mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
            self.pickup_group_of_units(selected_units, mouse_world_pos, placement_team)

    def update_group_partial_units_position(self, mouse_world_pos: Tuple[float, float], snap_to_grid: bool = False) -> None:
        """Update positions of group partial units to show actual clipped placement positions.
        
        Uses the same calculation logic as actual placement to ensure preview matches reality.
        """
        if not self.selected_group_partial_units:
            return
            
        esper.switch_world(self.battle_id)
        
        # Get existing unit positions to consider for grid snapping
        existing_positions = []
        if snap_to_grid:
            for ent, (pos, _) in esper.get_components(Position, UnitTypeComponent):
                if esper.has_component(ent, Placing):
                    continue
                existing_positions.append((pos.x, pos.y))
        
        # Calculate positions using the shared logic
        calculated_positions = self.calculate_group_positions(
            mouse_world_pos=mouse_world_pos,
            unit_offsets=self.group_unit_offsets,
            battle_hex_coords=self.battle.hex_coords,
            snap_to_grid=snap_to_grid,
            required_team=None if self.sandbox_mode else TeamType.TEAM1,
            current_unit_positions=existing_positions,
        )
        
        # Update partial unit positions
        for i, (partial_unit, new_pos) in enumerate(zip(self.selected_group_partial_units, calculated_positions)):
            if not esper.entity_exists(partial_unit):
                continue
            
            # Update partial unit position to show actual placement position
            pos = esper.component_for_entity(partial_unit, Position)
            pos.x, pos.y = new_pos
            esper.add_component(partial_unit, Focus())

    def draw_selection_rectangle(self) -> None:
        """Draw the selection rectangle during drag selection."""
        if not self.is_drag_selecting:
            return
            
        # Create rectangle from drag positions
        start_x, start_y = self.drag_start_pos
        end_x, end_y = self.drag_end_pos
        
        rect_x = min(start_x, end_x)
        rect_y = min(start_y, end_y)
        rect_w = abs(end_x - start_x)
        rect_h = abs(end_y - start_y)
        
        rect_w = max(rect_w, 1)
        rect_h = max(rect_h, 1)
        
        # Draw selection rectangle
        selection_rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)
        pygame.draw.rect(self.screen, (0, 255, 0), selection_rect, 2)
        
        # Draw semi-transparent fill
        selection_surface = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        selection_surface.fill((0, 255, 0, 50))
        self.screen.blit(selection_surface, (rect_x, rect_y))

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the sandbox scene."""
        esper.switch_world(self.battle_id)
        keys = pygame.key.get_pressed()
        show_grid = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Get battle hex coordinates
        battle = self.world_map_view.battles[self.battle_id]
        if battle.hex_coords is None:
            raise ValueError(f"Battle {self.battle_id} has no hex coordinates")
        battle_coords = battle.hex_coords
        world_x, _ = axial_to_world(*battle_coords)

        hovered_unit = get_hovered_unit(self.camera)
        hovered_team = esper.component_for_entity(hovered_unit, Team).type if hovered_unit is not None else None
        placement_pos = get_placement_pos(
            mouse_pos=pygame.mouse.get_pos(),
            battle_id=self.battle_id,
            hex_coords=battle_coords,
            camera=self.camera,
            snap_to_grid=show_grid,
            required_team=None if self.sandbox_mode else TeamType.TEAM1,
        )
        placement_team = TeamType.TEAM1 if placement_pos[0] < world_x else TeamType.TEAM2

        stop_drag_selecting = False
        for event in events:
            if event.type == pygame.QUIT:
                return False

            if self.handle_confirmation_dialog_keys(event):
                continue

            self.handle_escape(event)

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    for unit_count in self.barracks.unit_list_items:
                        if event.ui_element == unit_count.button:
                            play_intro(unit_count.unit_type)
                            # Create a single-unit group for placement
                            self.clear_group_pickup()  # Clear any existing group
                            self.group_unit_offsets = [(0, 0)]  # Single unit at mouse position
                            self.group_unit_types = [unit_count.unit_type]
                            self.group_placement_team = placement_team
                            
                            # Create transparent partial unit
                            mouse_pos = pygame.mouse.get_pos()
                            mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
                            partial_unit = create_unit(
                                x=mouse_world_pos[0],
                                y=mouse_world_pos[1],
                                unit_type=unit_count.unit_type,
                                team=placement_team,
                                corruption_powers=self.battle.corruption_powers
                            )
                            esper.add_component(partial_unit, Placing())
                            esper.add_component(partial_unit, Transparency(alpha=128))
                            self.selected_group_partial_units = [partial_unit]
                            
                            # Remove from barracks since we're carrying it
                            self.barracks.remove_unit(unit_count.unit_type)
                            
                            # Select the unit type in barracks UI
                            self.barracks.select_unit_type(unit_count.unit_type)
                            break
                    assert event.ui_element is not None
                    if event.ui_element == self.save_button:
                        enemy_placements = get_unit_placements(TeamType.TEAM2, self.battle)
                        ally_placements = get_unit_placements(TeamType.TEAM1, self.battle)
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            ally_placements=ally_placements,
                            enemy_placements=enemy_placements,
                            existing_battle_id=self.battle_id,
                        )
                    elif event.ui_element == self.return_button:
                        self.handle_return()
                        return super().update(time_delta, events)
                    elif event.ui_element == self.start_button:
                        pygame.event.post(
                            BattleSceneEvent(
                                world_map_view=self.world_map_view,
                                battle_id=self.battle_id,
                                sandbox_mode=self.sandbox_mode,
                            ).to_event()
                        )
                        return super().update(time_delta, events)
                    elif (self.save_dialog and 
                          event.ui_element == self.save_dialog.save_battle_button):
                        self.save_dialog.save_battle(is_test=False)
                        self.save_dialog.kill()
                        self.save_dialog = None
                    elif (self.save_dialog and 
                          event.ui_element == self.save_dialog.save_test_button):
                        self.save_dialog.save_battle(is_test=True)
                        self.save_dialog.kill()
                    elif (self.save_dialog and 
                          event.ui_element == self.save_dialog.cancel_button):
                        self.save_dialog.kill()
                        self.save_dialog = None
                    elif self.developer_mode and event.ui_element == self.edit_corruption_button:
                        # Open corruption power editor dialog
                        self.corruption_editor = CorruptionPowerEditorDialog(
                            manager=self.manager,
                            current_powers=self.battle.corruption_powers,
                            on_save=self._save_corruption_powers
                        )
                    elif self.developer_mode and event.ui_element == self.toggle_corruption_button:
                        # Toggle corruption state
                        self._toggle_corruption()
                    elif event.ui_element == self.simulate_button:
                        outcome = simulate_battle(
                            ally_placements=get_unit_placements(TeamType.TEAM1, self.battle),
                            enemy_placements=get_unit_placements(TeamType.TEAM2, self.battle),
                            max_duration=60,  # 60 second timeout
                            corruption_powers=self.battle.corruption_powers,
                        )
                        
                        # Update results box based on outcome
                        if outcome == BattleOutcome.TEAM1_VICTORY:
                            self.results_box.set_text('Team 1 Wins')
                        elif outcome == BattleOutcome.TEAM2_VICTORY:
                            self.results_box.set_text('Team 2 Wins')
                        elif outcome == BattleOutcome.TIMEOUT:
                            self.results_box.set_text('Timeout')
                    elif event.ui_element == self.clear_button:
                        self.clear_allied_units()
                elif event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if self.confirmation_dialog is not None and event.ui_element == self.confirmation_dialog:
                        self.world_map_view.move_camera_above_battle(self.battle_id)
                        self.world_map_view.rebuild(battles=progress_manager.get_battles_including_solutions())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)

            if event.type == pygame.MOUSEBUTTONDOWN and not mouse_over_ui(self.manager):
                if event.button == pygame.BUTTON_LEFT:
                    # If we have a group picked up, place them
                    if self.selected_group_partial_units:
                        mouse_world_pos = self.camera.screen_to_world(*event.pos)
                        self.place_group_units(mouse_world_pos, snap_to_grid=show_grid)
                    else:
                        self.is_drag_selecting = True
                        self.drag_start_pos = event.pos
                        self.drag_end_pos = event.pos
                        
                elif event.button == pygame.BUTTON_RIGHT:
                    # If we have a group picked up, cancel the pickup
                    if self.selected_group_partial_units:
                        self.cancel_group_pickup()
                    # If right clicking on a unit, remove it
                    elif hovered_unit is not None and (self.sandbox_mode or hovered_team == TeamType.TEAM1):
                        # Remove the unit and add back to barracks
                        unit_type = esper.component_for_entity(hovered_unit, UnitTypeComponent).type
                        self.world_map_view.remove_unit(self.battle_id, hovered_unit)
                        self.barracks.add_unit(unit_type)
                        if self.progress_panel is not None:
                            self.progress_panel.update_battle(self.battle)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT and self.is_drag_selecting:
                    self.select_units_in_rect(self.drag_start_pos, self.drag_end_pos)
                    stop_drag_selecting = True

            elif event.type == pygame.MOUSEMOTION:
                if self.is_drag_selecting:
                    # Update drag selection rectangle
                    self.drag_end_pos = event.pos

            # Handle escape key to cancel any active selection/pickup
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.selected_group_partial_units:
                    self.cancel_group_pickup()

            self.camera.process_event(event)
            self.manager.process_events(event)
            self.feedback_button.handle_event(event)
            self.barracks.handle_event(event)
            
            # Handle corruption editor dialog events if it exists
            if hasattr(self, 'corruption_editor'):
                # Check for button presses
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # Close the dialog if save button was pressed
                    if hasattr(event, 'ui_element') and hasattr(self.corruption_editor, 'save_button'):
                        if event.ui_element == self.corruption_editor.save_button:
                            delattr(self, 'corruption_editor')

        # Update preview for group partial units
        if self.selected_group_partial_units:
            mouse_world_pos = self.camera.screen_to_world(*pygame.mouse.get_pos())
            self.update_group_partial_units_position(mouse_world_pos, snap_to_grid=show_grid)

        # Only update camera if no dialog is focused
        if self.save_dialog is None or not self.save_dialog.dialog.alive():
            self.camera.update(time_delta)

        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        # Update and draw the world map view
        self.world_map_view.draw_map()
        # Draw the grid lines if shift is held
        if show_grid:
            draw_grid(self.screen, self.camera, battle_coords)

        # Draw the legal placement area
        if self.selected_group_partial_units:
            legal_area = get_legal_placement_area(
                self.battle_id,
                battle_coords,
                required_team=None if self.sandbox_mode else TeamType.TEAM1,
                include_units=False,
            )
            for polygon in legal_area.geoms if isinstance(legal_area, shapely.MultiPolygon) else [legal_area]:
                pygame.draw.lines(self.screen, (175, 175, 175), False, 
                    [self.camera.world_to_screen(x, y) for x, y in polygon.exterior.coords], 
                    width=2)
        # Draw white line down the middle of the hexagon
        center_line = get_center_line(battle_coords)
        pygame.draw.lines(
            self.screen,
            gc.MAP_BATTLEFIELD_EDGE_COLOR,
            False,
            [self.camera.world_to_screen(x, y) for x, y in center_line.coords],
            width=2,
        )

        self.world_map_view.update_battles(time_delta)
        # Update barracks selection - if we have a single unit group picked up, show that unit as selected
        if self.selected_group_partial_units and len(self.group_unit_types) == 1:
            self.barracks.select_unit_type(self.group_unit_types[0])
        else:
            self.barracks.select_unit_type(None)
        
        # Update selected unit manager for card animations
        selected_unit_manager.update(time_delta)
        
        # Draw selection UI elements
        self.draw_selection_rectangle()
        if stop_drag_selecting:
            self.is_drag_selecting = False
            self.drag_start_pos = None
            self.drag_end_pos = None
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)

    def _save_corruption_powers(self, powers: list[CorruptionPower]) -> None:
        """Save the corruption powers for the current battle."""
        self.battle.corruption_powers = powers
        if self.battle.id != "sandbox":
            battles.update_battle(self.battle, self.battle)
        
        # Make sure to update the world map
        self.world_map_view.rebuild(battles=self.world_map_view.battles.values())
        
        # Update corruption icon
        if self.corruption_icon is not None:
            self.corruption_icon.kill()
            self.corruption_icon = None

        if self.battle.hex_coords in self.world_map_view.corrupted_hexes:
            icon_size = (48, 48)
            icon_position = (pygame.display.Info().current_w - icon_size[0] - 15, 50)
            self.corruption_icon = CorruptionIcon(
                manager=self.manager,
                position=icon_position,
                size=icon_size,
                battle_hex_coords=self.battle.hex_coords,
                corruption_powers=powers
            )

    def _toggle_corruption(self) -> None:
        """Toggle the corruption state of the current battle."""
        # Get battle hex coordinates
        if self.battle.hex_coords is None:
            return
            
        # Toggle the corruption state
        if self.battle.hex_coords in self.world_map_view.corrupted_hexes:
            # Remove from corrupted hexes
            self.world_map_view.corrupted_hexes.remove(self.battle.hex_coords)
            
            # Remove corruption icon if it exists
            if self.corruption_icon is not None:
                self.corruption_icon.kill()
                self.corruption_icon = None
        else:
            # Add to corrupted hexes
            self.world_map_view.corrupted_hexes.append(self.battle.hex_coords)
            
            # Create corruption icon
            icon_size = (48, 48)
            icon_position = (pygame.display.Info().current_w - icon_size[0] - 15, 50)
            self.corruption_icon = CorruptionIcon(
                manager=self.manager,
                position=icon_position,
                size=icon_size,
                battle_hex_coords=self.battle.hex_coords,
                corruption_powers=self.battle.corruption_powers
            )
        
        # Rebuild the world to apply changes
        self.world_map_view.rebuild(battles=self.world_map_view.battles.values())



