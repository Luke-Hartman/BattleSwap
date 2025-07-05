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
import upgrade_hexes
from voice import play_intro
from world_map_view import FillState, HexState, WorldMapView
from scene_utils import draw_grid, get_center_line, get_placement_pos, get_hovered_unit, get_unit_placements, get_legal_placement_area, clip_to_polygon, has_unsaved_changes, mouse_over_ui, calculate_group_placement_positions
from ui_components.progress_panel import ProgressPanel
from ui_components.corruption_power_editor import CorruptionPowerEditorDialog
from corruption_powers import CorruptionPower
from selected_unit_manager import selected_unit_manager
from components.sprite_sheet import SpriteSheet
from components.unit_tier import UnitTier


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
        is_corrupted: bool = False,
        sandbox_mode: bool = False,
        developer_mode: bool = False,
    ):
        """Initialize the sandbox scene.
        
        Args:
            screen: The pygame surface to render to.
            manager: The pygame_gui manager for the scene.
            world_map_view: The world map view for the scene.
            battle_id: Which battle is focused.
            is_corrupted: Whether the battle is corrupted.
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
        self._selected_unit_type: Optional[UnitType] = None
        if world_map_view is None:
            battle = battles.Battle(
                id="sandbox",
                tip=["A customizable battle for experimenting"],
                hex_coords=(0, 0),
                allies=[],
                enemies=[],
                is_test=True,
            )
            world_map_view = WorldMapView(
                screen=self.screen,
                manager=self.manager,
                battles=[battle],
                camera=Camera(),
            )
            if battle_id is not None:
                raise ValueError("Battle ID must be None if world_map_view is None")
            battle_id = "sandbox"
        else:
            if battle_id is None:
                raise ValueError("Battle ID must be provided if world_map_view is not None")
            battle = world_map_view.battles[battle_id]
        self.world_map_view = world_map_view
        self.camera = world_map_view.camera
        self.battle_id = battle_id
        self.battle = battle
        self.is_corrupted = is_corrupted
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
                other_battle.hex_coords: HexState(fill=FillState.UNFOCUSED) if other_battle.hex_coords != battle.hex_coords else HexState(fill=FillState.NORMAL)
                for other_battle in self.world_map_view.battles.values()
            }
        else:
            # Set unfocused for all solved battles except the focused one
            # Set fogged for all unsolved battles
            unfocused_states = {}
            for other_battle in self.world_map_view.battles.values():
                if other_battle.hex_coords == battle.hex_coords:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.NORMAL)
                else:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.FOGGED)
        
        # Also fog all upgrade hexes during setup battle
        for upgrade_hex_coords in upgrade_hexes.get_upgrade_hexes():
            unfocused_states[upgrade_hex_coords] = HexState(fill=FillState.FOGGED)
        
        self.world_map_view.reset_hex_states()
        self.world_map_view.update_hex_state(unfocused_states)

        self.return_button = ReturnButton(self.manager)
        self.start_button = StartButton(self.manager)
        self.feedback_button = FeedbackButton(self.manager)
        self.tip_box = TipBox(self.manager, battle)
        
        if is_corrupted:
            icon_size = (48, 48)
            icon_position = (pygame.display.Info().current_w - icon_size[0] - 15, 50)
            self.corruption_icon = CorruptionIcon(
                manager=self.manager,
                position=icon_position,
                size=icon_size,
                battle_hex_coords=battle.hex_coords,
                corruption_powers=battle.corruption_powers
            )
        else:
            self.corruption_icon = None

        self.barracks = BarracksUI(
            self.manager,
            starting_units={} if self.sandbox_mode else progress_manager.available_units(battle),
            interactive=True,
            sandbox_mode=self.sandbox_mode,
            current_battle=battle,
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
                (pygame.display.Info().current_w - 295, barracks_bottom - 108),
                (235, 115)
            ),
            manager=self.manager,
            current_battle=battle,
            is_setup_mode=not self.battle.is_test,  # Only use setup mode for non-test battles
        ) if not self.sandbox_mode else None

        self.selected_partial_unit: Optional[int] = None

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
    
    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        """Get the currently selected unit type."""
        return self._selected_unit_type

    def set_selected_unit_type(
        self,
        value: Optional[UnitType],
        placement_team: TeamType,
    ) -> None:
        """Set the currently selected unit type."""
        self._selected_unit_type = value
        self.barracks.select_unit_type(value)
        if self.selected_partial_unit is not None:
            esper.delete_entity(self.selected_partial_unit)
        if value is None:
            self.selected_partial_unit = None
            return
        self.selected_partial_unit = create_unit(
            x=0,
            y=0,
            unit_type=value,
            team=placement_team,
            corruption_powers=self.battle.corruption_powers,
            tier=progress_manager.get_unit_tier(value) if value and placement_team == TeamType.TEAM1 else UnitTier.BASIC
        )
        esper.add_component(self.selected_partial_unit, Placing())
        # This shouldn't be needed anymore, but it used to be here, and so bugs
        # might be related to it not being disabled.
        # esper.remove_component(self.selected_partial_unit, UnitTypeComponent)
        esper.add_component(self.selected_partial_unit, Transparency(alpha=128))
    
    def create_unit_of_selected_type(self, placement_pos: Tuple[int, int], team: TeamType) -> None:
        """Create a unit of the selected type (as a group of size 1)."""
        assert self.sandbox_mode or team == TeamType.TEAM1
        self.world_map_view.add_unit(
            self.battle_id,
            self.selected_unit_type,
            placement_pos,
            team,
        )
        self.barracks.remove_unit(self.selected_unit_type)
        # Keep unit selected if there are more copies in the barracks
        if self.barracks.units[self.selected_unit_type] == 0:
            self.set_selected_unit_type(None, TeamType.TEAM1)
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)
    
    def remove_unit(self, unit_id: int) -> None:
        """Delete a unit of the selected type."""
        assert self.sandbox_mode or esper.component_for_entity(unit_id, Team).type == TeamType.TEAM1
        self.world_map_view.remove_unit(
            self.battle_id,
            unit_id,
        )
        unit_type = esper.component_for_entity(unit_id, UnitTypeComponent).type
        self.barracks.add_unit(unit_type)
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)

    def clear_allied_units(self) -> None:
        """Remove all allied units from the battlefield."""
        # Get all allied units in the current world
        esper.switch_world(self.battle_id)
        allied_units = []
        for ent, (team, _) in esper.get_components(Team, UnitTypeComponent):
            if team.type == TeamType.TEAM1 and not esper.has_component(ent, Placing):
                allied_units.append(ent)
        
        # Remove each allied unit
        for unit_id in allied_units:
            if esper.entity_exists(unit_id):  # Check if entity still exists before removing
                self.remove_unit(unit_id)

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
            pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())

    def pickup_group_of_units(self, unit_ids: List[int], mouse_world_pos: Tuple[float, float], placement_team: TeamType) -> None:
        """Pick up a group of units as transparent previews, like single unit pickup."""
        if not unit_ids:
            return
            
        esper.switch_world(self.battle_id)
        
        # Clear any existing single unit pickup
        if self.selected_partial_unit is not None:
            esper.delete_entity(self.selected_partial_unit)
            self.selected_partial_unit = None
        self.set_selected_unit_type(None, placement_team)
        
        # Clear existing group pickup
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
                corruption_powers=self.battle.corruption_powers,
                tier=progress_manager.get_unit_tier(unit_type_comp.type)
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
        
        # Determine final placement team (for sandbox mode, base on mouse position)
        battle_coords = self.battle.hex_coords
        if self.sandbox_mode:
            world_x, _ = axial_to_world(*battle_coords)
            final_placement_team = TeamType.TEAM1 if mouse_world_pos[0] < world_x else TeamType.TEAM2
        else:
            final_placement_team = self.group_placement_team
        
        # Use unified placement logic
        placement_positions = calculate_group_placement_positions(
            mouse_world_pos=mouse_world_pos,
            unit_offsets=self.group_unit_offsets,
            battle_id=self.battle_id,
            hex_coords=battle_coords,
            required_team=None if self.sandbox_mode else TeamType.TEAM1,
            snap_to_grid=snap_to_grid,
            sandbox_mode=self.sandbox_mode,
        )
        
        # Place each unit at its calculated position
        for i, unit_type in enumerate(self.group_unit_types):
            if i < len(placement_positions):
                self.world_map_view.add_unit(
                    self.battle_id,
                    unit_type,
                    placement_positions[i],
                    final_placement_team,
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
        
        This uses the same unified placement logic as actual placement to ensure 
        previews match the final placement positions exactly.
        """
        if not self.selected_group_partial_units:
            return
            
        esper.switch_world(self.battle_id)
        
        # Determine preview team (for sandbox mode, base on mouse position)
        battle_coords = self.battle.hex_coords
        if self.sandbox_mode:
            world_x, _ = axial_to_world(*battle_coords)
            preview_team = TeamType.TEAM1 if mouse_world_pos[0] < world_x else TeamType.TEAM2
            
            # Update partial unit teams if needed
            for partial_unit in self.selected_group_partial_units:
                if esper.entity_exists(partial_unit):
                    current_team = esper.component_for_entity(partial_unit, Team)
                    if current_team.type != preview_team:
                        current_team.type = preview_team
        
        # Use unified placement logic to calculate positions
        placement_positions = calculate_group_placement_positions(
            mouse_world_pos=mouse_world_pos,
            unit_offsets=self.group_unit_offsets,
            battle_id=self.battle_id,
            hex_coords=battle_coords,
            required_team=None if self.sandbox_mode else TeamType.TEAM1,
            snap_to_grid=snap_to_grid,
            sandbox_mode=self.sandbox_mode,
        )
        
        # Update each partial unit's position to show actual placement position
        for i, partial_unit in enumerate(self.selected_group_partial_units):
            if not esper.entity_exists(partial_unit) or i >= len(placement_positions):
                continue
                
            pos = esper.component_for_entity(partial_unit, Position)
            pos.x, pos.y = placement_positions[i]
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
                            self.set_selected_unit_type(unit_count.unit_type, placement_team)
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
                                current_scene_id=id(self),
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
                        pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())
                        return super().update(time_delta, events)

            if event.type == pygame.MOUSEBUTTONDOWN and not mouse_over_ui(self.manager):
                if event.button == pygame.BUTTON_LEFT:
                    # If we have a group picked up, place them
                    if self.selected_group_partial_units:
                        mouse_world_pos = self.camera.screen_to_world(*event.pos)
                        self.place_group_units(mouse_world_pos, snap_to_grid=show_grid)
                    # If we have a single unit selected, place it
                    elif self.selected_unit_type is not None:
                        click_placement_pos = get_placement_pos(
                            mouse_pos=event.pos,
                            battle_id=self.battle_id,
                            hex_coords=battle_coords,
                            camera=self.camera,
                            snap_to_grid=show_grid,
                            required_team=None if self.sandbox_mode else TeamType.TEAM1,
                        )
                        placement_team = TeamType.TEAM1 if click_placement_pos[0] < world_x else TeamType.TEAM2
                        self.create_unit_of_selected_type(click_placement_pos, placement_team)
                    else:
                        self.is_drag_selecting = True
                        self.drag_start_pos = event.pos
                        self.drag_end_pos = event.pos
                        
                elif event.button == pygame.BUTTON_RIGHT:
                    # If we have a group picked up, cancel the pickup
                    if self.selected_group_partial_units:
                        self.cancel_group_pickup()
                    # If we have a single unit selected, cancel it
                    elif self.selected_unit_type is not None:
                        self.set_selected_unit_type(None, placement_team)
                        emit_event(PLAY_SOUND, event=PlaySoundEvent(
                            filename="unit_picked_up.wav",
                            volume=0.5,
                        ))
                    # If right clicking on a unit, remove it
                    elif hovered_unit is not None and (self.sandbox_mode or hovered_team == TeamType.TEAM1):
                        self.remove_unit(hovered_unit)

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
                elif self.selected_unit_type is not None:
                    self.set_selected_unit_type(None, placement_team)
                else:
                    # Default escape handling
                    pass

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

        # Update preview for single selected unit
        if self.selected_partial_unit is not None:
            team = esper.component_for_entity(self.selected_partial_unit, Team)
            if team.type != placement_team:
                # If the partial unit is no longer on the side it was created on, recreate it
                self.set_selected_unit_type(self.selected_unit_type, placement_team)
            position = esper.component_for_entity(self.selected_partial_unit, Position)
            position.x, position.y = placement_pos
            esper.add_component(self.selected_partial_unit, Focus())

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
        if self.selected_unit_type is not None or self.selected_group_partial_units:
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
        self.barracks.select_unit_type(self.selected_unit_type)
        
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

        if self.is_corrupted:
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
        if self.is_corrupted:
            # Remove from corrupted hexes
            self.is_corrupted = False
            
            # Remove corruption icon if it exists
            if self.corruption_icon is not None:
                self.corruption_icon.kill()
                self.corruption_icon = None
        else:
            # Add to corrupted hexes
            self.is_corrupted = True
            
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



