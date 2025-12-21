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
from components.item import ItemComponent
from components.can_have_item import CanHaveItem
from components.spell import SpellComponent
from components.item import ItemType
from entities.units import create_unit
from events import CHANGE_MUSIC, PLAY_SOUND, ChangeMusicEvent, PlaySoundEvent, emit_event, UNMUTE_DRUMS, UnmuteDrumsEvent
from hex_grid import axial_to_world
from keyboard_shortcuts import format_button_text, KeyboardShortcuts
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

import upgrade_hexes
from voice import play_intro
from world_map_view import BorderState, FillState, HexState, WorldMapView, hex_lifecycle_to_fill_state
from scene_utils import draw_grid, get_center_line, get_placement_pos, get_hovered_unit, get_unit_placements, get_spell_placements, get_legal_placement_area, get_legal_spell_placement_area, has_unsaved_changes, mouse_over_ui, calculate_group_placement_positions, get_spell_placement_pos, clip_to_polygon
from ui_components.progress_panel import ProgressPanel
from ui_components.corruption_power_editor import CorruptionPowerEditorDialog
from corruption_powers import CorruptionPower
from selected_unit_manager import selected_unit_manager
from components.sprite_sheet import SpriteSheet
from components.unit_tier import UnitTier
from components.spell_type import SpellType
from components.spell import SpellComponent
from entities.spells import create_spell


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
        self._selected_item_type: Optional[ItemType] = None
        self._selected_spell_type: Optional[SpellType] = None
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
        
        # Multi-entity pickup state (like single entity pickup but for groups)
        self.selected_group_partial_units: List[int] = []  # List of partial unit entity IDs
        self.selected_group_partial_spells: List[int] = []  # List of partial spell entity IDs
        self.group_unit_offsets: List[Tuple[float, float]] = []  # Relative offsets from mouse for units
        self.group_spell_offsets: List[Tuple[float, float]] = []  # Relative offsets from mouse for spells
        self.group_unit_types: List[UnitType] = []  # Unit types for each partial unit
        self.group_spell_types: List[SpellType] = []  # Spell types for each partial spell
        self.group_unit_items: List[List[ItemType]] = []  # Items for each partial unit
        self.group_placement_team: Optional[TeamType] = None  # Team for the group
        
        if self.sandbox_mode:
            # Set unfocused states for all battles except the focused one
            unfocused_states = {}
            for other_battle in self.world_map_view.battles.values():
                if other_battle.hex_coords == battle.hex_coords:
                    hex_state = progress_manager.get_hex_state(battle.hex_coords)
                    fill_state = hex_lifecycle_to_fill_state(hex_state)
                    unfocused_states[other_battle.hex_coords] = HexState(fill=fill_state)
                else:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.UNCLAIMED)
        else:
            # Set unfocused for all solved battles except the focused one
            # Set fogged for all unsolved battles
            unfocused_states = {}
            for other_battle in self.world_map_view.battles.values():
                if other_battle.hex_coords == battle.hex_coords:
                    hex_state = progress_manager.get_hex_state(battle.hex_coords)
                    fill_state = hex_lifecycle_to_fill_state(hex_state)
                    if fill_state == FillState.UNCLAIMED:
                        fill_state = FillState.CLAIMED
                    unfocused_states[other_battle.hex_coords] = HexState(fill=fill_state)
                else:
                    hex_state = progress_manager.get_hex_state(other_battle.hex_coords)
                    fill_state = hex_lifecycle_to_fill_state(hex_state)
                    unfocused_states[other_battle.hex_coords] = HexState(fill=fill_state, fogged=True)
        
        # Also fog all upgrade hexes during setup battle
        for upgrade_hex_coords in upgrade_hexes.get_upgrade_hexes():
            hex_state = progress_manager.get_hex_state(upgrade_hex_coords)
            fill_state = hex_lifecycle_to_fill_state(hex_state)
            unfocused_states[upgrade_hex_coords] = HexState(fill=fill_state, fogged=True)
        
        self.world_map_view.reset_hex_states()
        self.world_map_view.update_hex_state(unfocused_states)

        self.return_button = ReturnButton(self.manager)
        self.start_button = StartButton(self.manager)
        self.feedback_button = FeedbackButton(self.manager)
        
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
            acquired_items={} if self.sandbox_mode else progress_manager.available_items(battle),
            acquired_spells={} if self.sandbox_mode else progress_manager.available_spells(battle),
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
        self.selected_spell: Optional[int] = None

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
        
        # Set initial start button state based on unit placement
        self._update_start_button_state()
    
    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        """Get the currently selected unit type."""
        return self._selected_unit_type
    
    @property
    def selected_item_type(self) -> Optional[ItemType]:
        """Get the currently selected item type."""
        return self._selected_item_type
    
    @property
    def selected_spell_type(self) -> Optional[SpellType]:
        """Get the currently selected spell type."""
        return self._selected_spell_type

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
        if self.selected_spell is not None:
            esper.delete_entity(self.selected_spell)
        self.cancel_group_pickup()
        if value is None:
            self.selected_partial_unit = None
            return
        self.set_selected_spell_type(None)
        self.set_selected_item_type(None)
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
    
    def set_selected_item_type(self, value: Optional[ItemType]) -> None:
        """Set the currently selected item type."""
        self._selected_item_type = value
        self.barracks.select_item_type(value)
        # Clear unit and spell selection when selecting an item
        if value is not None:
            self.set_selected_unit_type(None, TeamType.TEAM1)
            self.set_selected_spell_type(None)
            # Change cursor to indicate item placement mode
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
            # Add CanHaveItem component to all player units
            self._add_can_have_item_to_units()
        else:
            # Reset cursor to default
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            # Remove CanHaveItem component from all units
            self._remove_can_have_item_from_units()
    
    def set_selected_spell_type(self, value: Optional[SpellType]) -> None:
        """Set the currently selected spell type."""
        self._selected_spell_type = value
        self.barracks.select_spell_type(value)
        if self.selected_spell is not None:
            esper.delete_entity(self.selected_spell)
        self.cancel_group_pickup()
        if value is None:
            self.selected_spell = None
            return
        # Clear other selections when selecting a spell
        self.set_selected_unit_type(None, TeamType.TEAM1)
        self.set_selected_item_type(None)
        # Create spell entity that follows the cursor
        self.selected_spell = create_spell(
            x=0,
            y=0,
            spell_type=value,
            team=TeamType.TEAM1,  # Spells are always placed by the player
            corruption_powers=self.battle.corruption_powers
        )
        esper.add_component(self.selected_spell, Placing())
        esper.add_component(self.selected_spell, Transparency(alpha=128))
    
    def _add_can_have_item_to_units(self) -> None:
        """Add CanHaveItem component to all player units that meet the item's unit condition."""
        assert self._selected_item_type is not None
        
        # Get the item's unit condition
        from entities.items import item_registry
        item = item_registry[self._selected_item_type]
        unit_condition = item.get_unit_condition()
            
        for ent, (team,) in esper.get_components(Team):
            if team.type == TeamType.TEAM1 and not esper.has_component(ent, CanHaveItem):
                # Check if the unit meets the item's unit condition
                if unit_condition.check(ent):
                    esper.add_component(ent, CanHaveItem())
    
    def _remove_can_have_item_from_units(self) -> None:
        """Remove CanHaveItem component from all units."""
        for ent, _ in esper.get_components(CanHaveItem):
            esper.remove_component(ent, CanHaveItem)
    
    def create_unit_of_selected_type(self, placement_pos: Tuple[float, float], team: TeamType) -> None:
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
        if not self.barracks.has_unit_available(self.selected_unit_type):
            self.set_selected_unit_type(None, TeamType.TEAM1)
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)
    
    def try_place_item_on_unit(self, mouse_pos: Tuple[int, int]) -> None:
        """Try to place the selected item on a unit at the mouse position."""
        # Get the unit at the mouse position
        hovered_unit = get_hovered_unit(self.camera)
        
        if hovered_unit is not None:
            # Check if the unit is on the player's team (only allow placing items on player units)
            if esper.has_component(hovered_unit, Team):
                unit_team = esper.component_for_entity(hovered_unit, Team).type
                if unit_team == TeamType.TEAM1:
                    # Place the item on the unit
                    self.place_item_on_unit(hovered_unit, self.selected_item_type)
                    # Keep item selected if there are more copies in the barracks
                    if not self.barracks.has_item_available(self.selected_item_type):
                        self.set_selected_item_type(None)
                else:
                    # Can't place items on enemy units
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.3
                    ))
            else:
                # Unit has no team component, play error sound
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
        else:
            # No unit found at mouse position, play error sound
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.5
            ))
    
    def place_item_on_unit(self, unit_id: int, item_type: ItemType) -> None:
        """Place an item on a specific unit."""
        # Check if we have any items of this type available
        if not self.barracks.has_item_available(item_type):
            # No items available, play error sound
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.3
            ))
            return
        
        # Note: Removed restriction that prevented multiple items of the same type
        
        # Get unit data before removing it
        pos = esper.component_for_entity(unit_id, Position)
        unit_type_comp = esper.component_for_entity(unit_id, UnitTypeComponent)
        team = esper.component_for_entity(unit_id, Team)
        
        # Get current items and add the new item
        current_items = []
        if esper.has_component(unit_id, ItemComponent):
            item_component = esper.component_for_entity(unit_id, ItemComponent)
            current_items = item_component.items.copy()
        current_items.append(item_type)
        
        # Remove the unit from the battlefield
        self.world_map_view.remove_unit(self.battle_id, unit_id)
        
        # Remove the item from the barracks
        self.barracks.remove_item(item_type)
        
        # Recreate the unit with the updated items list
        entity = self.world_map_view.add_unit(
            self.battle_id,
            unit_type_comp.type,
            (pos.x, pos.y),
            team.type,
            items=current_items
        )
        
        # Update CanHaveItem components - remove from all units first, then add back to eligible ones
        self._remove_can_have_item_from_units()
        if self._selected_item_type is not None:
            self._add_can_have_item_to_units()
        
        # Play success sound
        emit_event(PLAY_SOUND, event=PlaySoundEvent(
            filename="unit_placed.wav",
            volume=0.5
        ))
        
        # Update progress panel if it exists
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)
    
    def try_place_spell(self, mouse_pos: Tuple[int, int]) -> None:
        """Try to place the selected spell at the preview position."""
        
        # Check if we have any spells of this type available
        if not self.barracks.has_spell_available(self.selected_spell_type):
            # No spells available, play error sound
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.3
            ))
            return
        
        # Use the position from the preview spell instead of recalculating
        position = esper.component_for_entity(self.selected_spell, Position)
        placement_pos = (position.x, position.y)
        
        # Place the spell at the preview position
        self.place_spell(placement_pos, self.selected_spell_type)
        
        # Keep spell selected if there are more copies in the barracks
        if not self.barracks.has_spell_available(self.selected_spell_type):
            self.set_selected_spell_type(None)
    
    def place_spell(self, world_pos: Tuple[float, float], spell_type: SpellType) -> None:
        """Place a spell at the specified world position."""
        
        # Create the spell entity
        spell_entity = create_spell(
            x=world_pos[0],
            y=world_pos[1],
            spell_type=spell_type,
            team=TeamType.TEAM1,  # Spells are always placed by the player
            corruption_powers=self.battle.corruption_powers
        )
        
        # Add the spell to the world map view
        self.world_map_view.add_spell(self.battle_id, spell_entity)
        
        # Remove the spell from the barracks
        self.barracks.remove_spell(spell_type)
        
        # Play success sound
        emit_event(PLAY_SOUND, event=PlaySoundEvent(
            filename="unit_placed.wav",
            volume=0.5
        ))
        
        # Update progress panel if it exists
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)
    
    def _is_hovering_spell(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if the mouse is hovering over a spell handle."""
        mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
        
        for ent, (pos, spell_component) in esper.get_components(Position, SpellComponent):
            # Check if mouse is within the spell's handle (not the full radius)
            distance = ((mouse_world_pos[0] - pos.x) ** 2 + (mouse_world_pos[1] - pos.y) ** 2) ** 0.5
            if distance <= gc.SPELL_HANDLE_SIZE:
                return True
        return False
    
    def remove_hovered_spell(self, mouse_pos: Tuple[int, int]) -> None:
        """Remove the spell that the mouse is hovering over."""
        mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
        
        for ent, (pos, spell_component) in esper.get_components(Position, SpellComponent):
            # Check if mouse is within the spell's handle (not the full radius)
            distance = ((mouse_world_pos[0] - pos.x) ** 2 + (mouse_world_pos[1] - pos.y) ** 2) ** 0.5
            if distance <= gc.SPELL_HANDLE_SIZE:
                # Remove the spell from the world map view
                self.world_map_view.remove_spell(self.battle_id, ent)
                
                # Add the spell back to the barracks
                self.barracks.add_spell(spell_component.spell_type)
                
                # Play sound
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="unit_returned.wav",
                    volume=0.5
                ))
                
                # Update progress panel if it exists
                if self.progress_panel is not None:
                    self.progress_panel.update_battle(self.battle)
                break
    
    def remove_unit(self, unit_id: int) -> None:
        """Delete a unit of the selected type."""
        assert self.sandbox_mode or esper.component_for_entity(unit_id, Team).type == TeamType.TEAM1
        
        # Get unit's items before removing the unit
        unit_items = []
        if esper.has_component(unit_id, ItemComponent):
            item_component = esper.component_for_entity(unit_id, ItemComponent)
            unit_items = item_component.items.copy()
        
        unit_type = esper.component_for_entity(unit_id, UnitTypeComponent).type
        self.world_map_view.remove_unit(
            self.battle_id,
            unit_id,
        )
        self.barracks.add_unit(unit_type)
        
        # Return items to barracks
        for item_type in unit_items:
            self.barracks.add_item(item_type)
        
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
            action_short_name=format_button_text("Exit", KeyboardShortcuts.SPACE),
            blocking=True
        )

    def handle_return(self) -> None:
        """Handle return button press or escape key."""
        if (
            not self.sandbox_mode and has_unsaved_changes(self.battle, get_unit_placements(TeamType.TEAM1, self.battle))
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

    def pickup_group_of_entities(self, unit_ids: List[int], spell_ids: List[int], mouse_world_pos: Tuple[float, float], placement_team: TeamType) -> None:
        """Pick up a group of units and spells as transparent previews, like single entity pickup."""
        if not unit_ids and not spell_ids:
            return
            
        esper.switch_world(self.battle_id)
        
        # Clear any existing single entity pickup
        if self.selected_partial_unit is not None:
            esper.delete_entity(self.selected_partial_unit)
            self.selected_partial_unit = None
        if self.selected_spell is not None:
            esper.delete_entity(self.selected_spell)
            self.selected_spell = None
        self.set_selected_unit_type(None, placement_team)
        self.set_selected_spell_type(None)
        
        # Clear existing group pickup
        self.clear_group_pickup()
        
        # Calculate center of selected entities for centering on mouse
        all_positions = []
        for unit_id in unit_ids:
            if esper.entity_exists(unit_id):
                pos = esper.component_for_entity(unit_id, Position)
                all_positions.append((pos.x, pos.y))
        for spell_id in spell_ids:
            if esper.entity_exists(spell_id):
                pos = esper.component_for_entity(spell_id, Position)
                all_positions.append((pos.x, pos.y))
        
        if not all_positions:
            return
            
        center_x = sum(pos[0] for pos in all_positions) / len(all_positions)
        center_y = sum(pos[1] for pos in all_positions) / len(all_positions)
        
        # Handle units
        for unit_id in unit_ids:
            if not esper.entity_exists(unit_id):
                continue
                
            pos = esper.component_for_entity(unit_id, Position)
            unit_type_comp = esper.component_for_entity(unit_id, UnitTypeComponent)
            
            # Get unit's items before removing the unit
            unit_items = []
            if esper.has_component(unit_id, ItemComponent):
                item_component = esper.component_for_entity(unit_id, ItemComponent)
                unit_items = item_component.items.copy()
            
            # Calculate offset from group center
            offset_x = pos.x - center_x
            offset_y = pos.y - center_y
            self.group_unit_offsets.append((offset_x, offset_y))
            self.group_unit_types.append(unit_type_comp.type)
            self.group_unit_items.append(unit_items)  # Store items for this unit
            
            # Create transparent partial unit with items
            partial_unit = create_unit(
                x=mouse_world_pos[0] + offset_x,
                y=mouse_world_pos[1] + offset_y,
                unit_type=unit_type_comp.type,
                team=placement_team,
                corruption_powers=self.battle.corruption_powers,
                tier=progress_manager.get_unit_tier(unit_type_comp.type),
                items=unit_items  # Pass the items to the new unit
            )
            esper.add_component(partial_unit, Placing())
            esper.add_component(partial_unit, Transparency(alpha=128))
            self.selected_group_partial_units.append(partial_unit)
            
            # Remove original unit from battlefield (but don't add to barracks since we're carrying them)
            self.world_map_view.remove_unit(self.battle_id, unit_id)
        
        # Handle spells
        for spell_id in spell_ids:
            if not esper.entity_exists(spell_id):
                continue
                
            pos = esper.component_for_entity(spell_id, Position)
            spell_component = esper.component_for_entity(spell_id, SpellComponent)
            
            # Calculate offset from group center
            offset_x = pos.x - center_x
            offset_y = pos.y - center_y
            self.group_spell_offsets.append((offset_x, offset_y))
            self.group_spell_types.append(spell_component.spell_type)
            
            # Create transparent partial spell
            partial_spell = create_spell(
                x=mouse_world_pos[0] + offset_x,
                y=mouse_world_pos[1] + offset_y,
                spell_type=spell_component.spell_type,
                team=placement_team,
                corruption_powers=self.battle.corruption_powers
            )
            esper.add_component(partial_spell, Placing())
            esper.add_component(partial_spell, Transparency(alpha=128))
            self.selected_group_partial_spells.append(partial_spell)
            
            # Remove original spell from battlefield (but don't add to barracks since we're carrying them)
            self.world_map_view.remove_spell(self.battle_id, spell_id)
        
        self.group_placement_team = placement_team

    def _recreate_group_partial_units(self, new_team: TeamType) -> None:
        """Recreate all group partial units with a new team."""
        if not self.selected_group_partial_units:
            return
            
        esper.switch_world(self.battle_id)
        
        # Get current mouse position to place recreated units
        mouse_pos = pygame.mouse.get_pos()
        mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
        
        # Delete existing partial units
        for partial_unit in self.selected_group_partial_units:
            if esper.entity_exists(partial_unit):
                esper.delete_entity(partial_unit)
        
        # Clear the list and recreate units
        self.selected_group_partial_units.clear()
        
        # Recreate partial units with new team
        for i, unit_type in enumerate(self.group_unit_types):
            if i < len(self.group_unit_offsets):
                offset_x, offset_y = self.group_unit_offsets[i]
                unit_items = self.group_unit_items[i] if i < len(self.group_unit_items) else []
                
                # Create transparent partial unit with new team and items
                partial_unit = create_unit(
                    x=mouse_world_pos[0] + offset_x,
                    y=mouse_world_pos[1] + offset_y,
                    unit_type=unit_type,
                    team=new_team,
                    corruption_powers=self.battle.corruption_powers,
                    tier=progress_manager.get_unit_tier(unit_type),
                    items=unit_items
                )
                esper.add_component(partial_unit, Placing())
                esper.add_component(partial_unit, Transparency(alpha=128))
                self.selected_group_partial_units.append(partial_unit)
        
        # Update the group placement team
        self.group_placement_team = new_team

    def clear_group_pickup(self) -> None:
        """Clear the group pickup state and delete partial units and spells."""
        esper.switch_world(self.battle_id)
        
        # Delete all partial units
        for partial_unit in self.selected_group_partial_units:
            if esper.entity_exists(partial_unit):
                esper.delete_entity(partial_unit)
        
        # Delete all partial spells
        for partial_spell in self.selected_group_partial_spells:
            if esper.entity_exists(partial_spell):
                esper.delete_entity(partial_spell)
        
        # Clear state
        self.selected_group_partial_units.clear()
        self.selected_group_partial_spells.clear()
        self.group_unit_offsets.clear()
        self.group_spell_offsets.clear()
        self.group_unit_types.clear()
        self.group_spell_types.clear()
        self.group_unit_items.clear()
        self.group_placement_team = None

    def place_group_entities(self, mouse_world_pos: Tuple[float, float], snap_to_grid: bool = False) -> None:
        """Place all units and spells from the group pickup."""
        if not (self.selected_group_partial_units or self.selected_group_partial_spells) or self.group_placement_team is None:
            return
            
        esper.switch_world(self.battle_id)
        
        # Determine placement team
        battle_coords = self.battle.hex_coords
        world_x, _ = axial_to_world(*battle_coords)
        
        if self.sandbox_mode:
            # In sandbox mode, all entities go to the side determined by mouse position
            placement_team = TeamType.TEAM1 if mouse_world_pos[0] < world_x else TeamType.TEAM2
        else:
            # In non-sandbox mode, always place on team 1 side
            placement_team = TeamType.TEAM1
        
        # Use unified placement logic for units
        if self.group_unit_offsets:
            placement_positions = calculate_group_placement_positions(
                mouse_world_pos=mouse_world_pos,
                unit_offsets=self.group_unit_offsets,
                battle_id=self.battle_id,
                hex_coords=battle_coords,
                required_team=placement_team,
                snap_to_grid=snap_to_grid,
                sandbox_mode=self.sandbox_mode,
            )
            
            # Place each unit at its calculated position
            for i, unit_type in enumerate(self.group_unit_types):
                if i < len(placement_positions):
                    unit_items = self.group_unit_items[i] if i < len(self.group_unit_items) else []
                    self.world_map_view.add_unit(
                        self.battle_id,
                        unit_type,
                        placement_positions[i],
                        placement_team,
                        items=unit_items
                    )
        
        # Place spells at their offset positions
        for i, spell_type in enumerate(self.group_spell_types):
            if i < len(self.group_spell_offsets):
                offset_x, offset_y = self.group_spell_offsets[i]
                spell_pos = (mouse_world_pos[0] + offset_x, mouse_world_pos[1] + offset_y)
                
                # Create the spell entity
                spell_entity = create_spell(
                    x=spell_pos[0],
                    y=spell_pos[1],
                    spell_type=spell_type,
                    team=placement_team,
                    corruption_powers=self.battle.corruption_powers
                )
                
                # Add the spell to the world map view
                self.world_map_view.add_spell(self.battle_id, spell_entity)
        
        # Clear the group pickup
        self.clear_group_pickup()
        
        if self.progress_panel is not None:
            self.progress_panel.update_battle(self.battle)

    def cancel_group_pickup(self) -> None:
        """Cancel group pickup and return units, items, and spells to barracks."""
        if not (self.selected_group_partial_units or self.selected_group_partial_spells):
            return
            
        # Return units to barracks inventory
        for unit_type in self.group_unit_types:
            self.barracks.add_unit(unit_type)
        
        # Return items to barracks inventory
        for unit_items in self.group_unit_items:
            for item_type in unit_items:
                self.barracks.add_item(item_type)
        
        # Return spells to barracks inventory
        for spell_type in self.group_spell_types:
            self.barracks.add_spell(spell_type)
        
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

    def select_units_in_rect(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float]) -> None:
        """Select all units and spells within the given screen rectangle and pick them up."""
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
        selected_spells = []
        placement_team = None
        
        # Select units
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
        
        # Select spells
        for ent, (pos, spell_component) in esper.get_components(Position, SpellComponent):
            if esper.has_component(ent, Placing):
                continue
            
            # Check if spell is within selection rectangle (spells use handle size for selection)
            distance = ((pos.x - (min_x + max_x) / 2) ** 2 + (pos.y - (min_y + max_y) / 2) ** 2) ** 0.5
            handle_size = gc.SPELL_HANDLE_SIZE
            if (pos.x >= min_x - handle_size and pos.x <= max_x + handle_size and 
                pos.y >= min_y - handle_size and pos.y <= max_y + handle_size):
                selected_spells.append(ent)
                if placement_team is None:
                    # For spells, default to team 1 (player team)
                    placement_team = TeamType.TEAM1
        
        # If entities were selected, pick them up
        if (selected_units or selected_spells) and placement_team is not None:
            # Calculate mouse world position for centering
            mouse_pos = pygame.mouse.get_pos()
            mouse_world_pos = self.camera.screen_to_world(*mouse_pos)
            self.pickup_group_of_entities(selected_units, selected_spells, mouse_world_pos, placement_team)

    def update_group_partial_entities_position(self, mouse_world_pos: Tuple[float, float], snap_to_grid: bool = False) -> None:
        """Update positions of group partial units and spells to show actual clipped placement positions.
        
        This uses the same unified placement logic as actual placement to ensure 
        previews match the final placement positions exactly.
        """
        if not (self.selected_group_partial_units or self.selected_group_partial_spells):
            return
            
        esper.switch_world(self.battle_id)
        
        # Determine preview team
        battle_coords = self.battle.hex_coords
        world_x, _ = axial_to_world(*battle_coords)
        
        if self.sandbox_mode:
            # In sandbox mode, all entities follow the mouse to either side
            preview_team = TeamType.TEAM1 if mouse_world_pos[0] < world_x else TeamType.TEAM2
            
            # Check if team changed and recreate partial units if needed
            if (self.selected_group_partial_units and 
                esper.entity_exists(self.selected_group_partial_units[0])):
                current_team = esper.component_for_entity(self.selected_group_partial_units[0], Team)
                if current_team.type != preview_team:
                    # Team changed, recreate all partial units with new team
                    self._recreate_group_partial_units(preview_team)
        else:
            # In non-sandbox mode, always use team 1
            preview_team = TeamType.TEAM1
        
        # Use unified placement logic to calculate positions for units
        if self.group_unit_offsets:
            placement_positions = calculate_group_placement_positions(
                mouse_world_pos=mouse_world_pos,
                unit_offsets=self.group_unit_offsets,
                battle_id=self.battle_id,
                hex_coords=battle_coords,
                required_team=preview_team,
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
        
        # Update spell positions to follow mouse with their offsets, clipped to legal area
        for i, partial_spell in enumerate(self.selected_group_partial_spells):
            if not esper.entity_exists(partial_spell) or i >= len(self.group_spell_offsets):
                continue
                
            offset_x, offset_y = self.group_spell_offsets[i]
            ideal_x = mouse_world_pos[0] + offset_x
            ideal_y = mouse_world_pos[1] + offset_y
            
            # Clip to legal spell placement area
            legal_area = get_legal_spell_placement_area(self.battle_id, battle_coords)
            clipped_pos = clip_to_polygon(legal_area, ideal_x, ideal_y)
            
            pos = esper.component_for_entity(partial_spell, Position)
            pos.x, pos.y = clipped_pos
            esper.add_component(partial_spell, Focus())

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
        
        # Calculate spell placement position separately
        spell_placement_pos = get_spell_placement_pos(
            mouse_pos=pygame.mouse.get_pos(),
            battle_id=self.battle_id,
            hex_coords=battle_coords,
            camera=self.camera,
            snap_to_grid=show_grid,
        )

        stop_drag_selecting = False
        for event in events:
            if event.type == pygame.QUIT:
                return False

            if self.handle_confirmation_dialog_keys(event):
                continue
            
            if self.handle_confirmation_dialog_events(event):
                continue

            self.handle_escape(event)
            
            # Handle Space key to start battle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Only start battle if there are allied units placed
                if self._has_allied_units_placed():
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.5
                    ))
                    pygame.event.post(
                        BattleSceneEvent(
                            current_scene_id=id(self),
                            world_map_view=self.world_map_view,
                            battle_id=self.battle_id,
                            sandbox_mode=self.sandbox_mode,
                        ).to_event()
                    )
                    return super().update(time_delta, events)
            
            # Handle number keys for unit selection from barracks
            if event.type == pygame.KEYDOWN and ((event.key >= pygame.K_1 and event.key <= pygame.K_9) or event.key == pygame.K_0):
                if event.key == pygame.K_0:
                    index = 9  # 0 key corresponds to 10th position (index 9)
                else:
                    index = event.key - pygame.K_1  # Convert to 0-based index
                
                # Get item at the specified index
                result = self.barracks.get_item_at_index(index)
                if result is not None:
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.5
                    ))
                # Check the type directly using isinstance
                if isinstance(result, UnitType):
                    play_intro(result)
                    self.set_selected_unit_type(result, placement_team)
                elif isinstance(result, ItemType):
                    self.set_selected_item_type(result)
                elif isinstance(result, SpellType):
                    self.set_selected_spell_type(result)

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    result = self.barracks.handle_button_press(event.ui_element)
                    if result is not None:
                        emit_event(PLAY_SOUND, event=PlaySoundEvent(
                            filename="ui_click.wav",
                            volume=0.5
                        ))
                    # Check the type directly using isinstance
                    if isinstance(result, UnitType):
                        play_intro(result)
                        self.set_selected_unit_type(result, placement_team)
                    elif isinstance(result, ItemType):
                        self.set_selected_item_type(result)
                    elif isinstance(result, SpellType):
                        self.set_selected_spell_type(result)
                    
                    assert event.ui_element is not None
                    if event.ui_element == self.save_button:
                        enemy_placements = get_unit_placements(TeamType.TEAM2, self.battle)
                        ally_placements = get_unit_placements(TeamType.TEAM1, self.battle)
                        spell_placements = get_spell_placements(TeamType.TEAM1, self.battle)
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            ally_placements=ally_placements,
                            enemy_placements=enemy_placements,
                            existing_battle_id=self.battle_id,
                            spell_placements=spell_placements,
                        )
                    elif event.ui_element == self.return_button:
                        self.handle_return()
                        return super().update(time_delta, events)
                    elif event.ui_element == self.start_button:
                        # Only start battle if there are allied units placed
                        if self._has_allied_units_placed():
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
                            hex_coords=self.battle.hex_coords if self.battle.hex_coords is not None else (0, 0),
                            corruption_powers=self.battle.corruption_powers,
                            spell_placements=self.battle.spells,
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
                        self.confirmation_dialog = None
                        self.world_map_view.move_camera_above_battle(self.battle_id)
                        self.world_map_view.rebuild(battles=progress_manager.get_battles_including_solutions())
                        pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())
                        return super().update(time_delta, events)

            if event.type == pygame.MOUSEBUTTONDOWN and not mouse_over_ui(self.manager):
                if event.button == pygame.BUTTON_LEFT:
                    # If we have a group picked up, place them
                    if self.selected_group_partial_units or self.selected_group_partial_spells:
                        mouse_world_pos = self.camera.screen_to_world(*event.pos)
                        self.place_group_entities(mouse_world_pos, snap_to_grid=show_grid)
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
                    elif self.selected_item_type is not None:
                        self.try_place_item_on_unit(event.pos)
                    elif self.selected_spell_type is not None:
                        self.try_place_spell(event.pos)
                    else:
                        self.is_drag_selecting = True
                        self.drag_start_pos = event.pos
                        self.drag_end_pos = event.pos
                        
                elif event.button == pygame.BUTTON_RIGHT:
                    # If we have a group picked up, cancel the pickup
                    if self.selected_group_partial_units or self.selected_group_partial_spells:
                        self.cancel_group_pickup()
                    # If we have a single unit selected, cancel it
                    elif self.selected_unit_type is not None:
                        self.set_selected_unit_type(None, placement_team)
                        emit_event(PLAY_SOUND, event=PlaySoundEvent(
                            filename="unit_picked_up.wav",
                            volume=0.5,
                        ))
                    # If we have an item selected, cancel it
                    elif self.selected_item_type is not None:
                        self.set_selected_item_type(None)
                        emit_event(PLAY_SOUND, event=PlaySoundEvent(
                            filename="ui_click.wav",
                            volume=0.5,
                        ))
                    # If we have a spell selected, cancel it
                    elif self.selected_spell_type is not None:
                        self.set_selected_spell_type(None)
                        emit_event(PLAY_SOUND, event=PlaySoundEvent(
                            filename="ui_click.wav",
                            volume=0.5,
                        ))
                    # If right clicking on a unit, remove it
                    elif hovered_unit is not None and (self.sandbox_mode or hovered_team == TeamType.TEAM1):
                        self.remove_unit(hovered_unit)
                    # If right clicking on a spell, remove it
                    elif self._is_hovering_spell(event.pos):
                        self.remove_hovered_spell(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT and self.is_drag_selecting:
                    self.select_units_in_rect(self.drag_start_pos, self.drag_end_pos)
                    stop_drag_selecting = True

            elif event.type == pygame.MOUSEMOTION:
                if self.is_drag_selecting:
                    # Update drag selection rectangle
                    self.drag_end_pos = event.pos



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

        # Update preview for selected spell
        if self.selected_spell is not None:
            position = esper.component_for_entity(self.selected_spell, Position)
            position.x, position.y = spell_placement_pos
            esper.add_component(self.selected_spell, Focus())

        # Update preview for group partial entities
        if self.selected_group_partial_units or self.selected_group_partial_spells:
            mouse_world_pos = self.camera.screen_to_world(*pygame.mouse.get_pos())
            self.update_group_partial_entities_position(mouse_world_pos, snap_to_grid=show_grid)

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
        if self.selected_unit_type is not None or self.selected_group_partial_units or self.selected_group_partial_spells:
            # Check if this is a spell-only group selection
            is_spell_only_group = (self.selected_group_partial_spells and 
                                 not self.selected_group_partial_units and 
                                 self.selected_unit_type is None)
            
            if is_spell_only_group:
                # For spell-only groups, show the entire battlefield like individual spells
                legal_area = get_legal_spell_placement_area(
                    self.battle_id,
                    battle_coords,
                )
            else:
                # For units or mixed groups, use team-restricted area
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
        if self.selected_spell is not None:
            legal_area = get_legal_spell_placement_area(
                self.battle_id,
                battle_coords,
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
        self.barracks.select_item_type(self.selected_item_type)
        
        # Update selected unit manager for card animations
        selected_unit_manager.update(time_delta)
        
        # Update start button state based on unit placement
        self._update_start_button_state()
        
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

    def _has_allied_units_placed(self) -> bool:
        """Check if any allied units are placed on the battlefield."""
        ally_placements = get_unit_placements(TeamType.TEAM1, self.battle)
        return len(ally_placements) > 0

    def _update_start_button_state(self) -> None:
        """Update the start button enabled/disabled state based on unit placement."""
        if self._has_allied_units_placed():
            self.start_button.enable()
            self.start_button.set_tooltip("Start the battle")
        else:
            self.start_button.disable()
            self.start_button.set_tooltip("Place at least one unit to start the battle")

    def _close_scene_windows(self) -> bool:
        """Close any open windows specific to the setup battle scene."""
        windows_closed = False
        
        # Handle special escape logic for entity selections first
        if self.selected_group_partial_units or self.selected_group_partial_spells:
            self.cancel_group_pickup()
            windows_closed = True
        if self.selected_unit_type is not None:
            # Get placement team - this mirrors the logic from the update method
            placement_team = TeamType.TEAM1 if not self.sandbox_mode else TeamType.TEAM2
            self.set_selected_unit_type(None, placement_team)
            windows_closed = True
            
        # Handle item selection cleanup
        if self.selected_item_type is not None:
            self.set_selected_item_type(None)
            windows_closed = True
            
        # Check for save dialog
        if hasattr(self, 'save_dialog') and self.save_dialog is not None and self.save_dialog.dialog.alive():
            self.save_dialog.dialog.kill()
            self.save_dialog = None
            windows_closed = True
            
        # Check for corruption editor dialog
        if hasattr(self, 'corruption_editor') and self.corruption_editor is not None:
            self.corruption_editor.kill()
            delattr(self, 'corruption_editor')
            windows_closed = True
            
        # Check for corruption power editor dialog
        if hasattr(self, 'corruption_power_editor') and self.corruption_power_editor is not None:
            self.corruption_power_editor.kill()
            self.corruption_power_editor = None
            windows_closed = True
            
        # Fall back to base class behavior and combine results
        return super()._close_scene_windows() or windows_closed



