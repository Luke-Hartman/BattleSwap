from collections import defaultdict
from game_constants import gc
from typing import List, Tuple, Optional

import pygame
import pygame_gui

from battles import get_battles, update_battle, Battle
import battles
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from progress_manager import HexLifecycleState, progress_manager
from scene_utils import mouse_over_ui
from scenes.events import PreviousSceneEvent, SetupBattleSceneEvent
from scenes.scene import Scene
from ui_components.return_button import ReturnButton
from world_map_view import BorderState, FillState, WorldMapView, HexState
import upgrade_hexes
from ui_components.tip_box import TipBox
from ui_components.save_battle_dialog import SaveBattleDialog
from ui_components.corruption_icon import CorruptionIcon
from selected_unit_manager import selected_unit_manager
from components.unit_type import UnitType

class CampaignEditorScene(Scene):
    """Scene for editing the campaign."""
    
    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        world_map_view: WorldMapView,
    ) -> None:
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.world_map_view = world_map_view

        self.hovered_hex: Optional[Tuple[int, int]] = None
        self.selected_hex: Optional[Tuple[int, int]] = None
        self.move_target_hex: Optional[Tuple[int, int]] = None
        self.corrupted_hexes: List[Tuple[int, int]] = list(hex_coords for hex_coords, state in progress_manager.hex_states.items() if state in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED])

        # Store context buttons
        self.context_buttons: dict[str, pygame_gui.elements.UIButton] = {}
        # Store UI elements for battle info
        self.battle_id_label: Optional[pygame_gui.elements.UILabel] = None
        self.tip_box: Optional[TipBox] = None
        self.corruption_icon: Optional[CorruptionIcon] = None
        
        # Store UI elements for campaign statistics
        self.unit_types_label: Optional[pygame_gui.elements.UILabel] = None
        self.upgrade_hexes_label: Optional[pygame_gui.elements.UILabel] = None
        
        self.create_ui()

    def get_unique_unit_types_count(self) -> int:
        """Get the count of unique unit types across all battles."""
        unique_unit_types = set()
        
        for battle in get_battles():
            # Count enemy unit types
            for unit_type, _ in battle.enemies:
                unique_unit_types.add(unit_type)
            
            # Count allied unit types if they exist
            if battle.allies:
                for unit_type, _ in battle.allies:
                    unique_unit_types.add(unit_type)
        
        return len(unique_unit_types)

    def create_ui(self) -> None:
        """Create the UI elements for the world map scene."""
        button_width = 100
        button_height = 40
        padding = 10
        
        self.return_button = ReturnButton(
            manager=self.manager,
        )
        
        # Create campaign statistics display
        self.create_statistics_display()

    def create_statistics_display(self) -> None:
        """Create the statistics display showing unit types and upgrade hex counts."""
        # Clear existing statistics labels
        if self.unit_types_label is not None:
            self.unit_types_label.kill()
            self.unit_types_label = None
        if self.upgrade_hexes_label is not None:
            self.upgrade_hexes_label.kill()
            self.upgrade_hexes_label = None
        
        # Calculate statistics
        unique_unit_types_count = self.get_unique_unit_types_count()
        upgrade_hexes_count = len(upgrade_hexes.get_upgrade_hexes())
        
        # Position for statistics display (top right corner)
        screen_width = pygame.display.Info().current_w
        label_width = 200
        label_height = 30
        padding = 10
        
        # Unit types count label
        self.unit_types_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (screen_width - label_width - padding, padding),
                (label_width, label_height)
            ),
            text=f"Unit Types: {unique_unit_types_count}",
            manager=self.manager
        )
        
        # Upgrade hexes count label
        self.upgrade_hexes_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (screen_width - label_width - padding, padding + label_height + 5),
                (label_width, label_height)
            ),
            text=f"Upgrade Hexes: {upgrade_hexes_count}",
            manager=self.manager
        )

    def update_battle_info(self, battle: Optional[Battle]) -> None:
        """Update the battle information display."""
        # Clear existing info
        if self.battle_id_label is not None:
            self.battle_id_label.kill()
            self.battle_id_label = None
        if self.tip_box is not None:
            self.tip_box.kill()
            self.tip_box = None
        if self.corruption_icon is not None:
            self.corruption_icon.kill()
            self.corruption_icon = None

        if battle is not None:
            # Create battle ID label
            self.battle_id_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((120, 10), (300, 40)),
                text=battle.id,
                manager=self.manager
            )
            # Create tip box
            self.tip_box = TipBox(self.manager, battle)
            
            # Show corruption icon if battle is corrupted
            if battle.hex_coords in self.corrupted_hexes:
                icon_size = (48, 48)
                icon_position = (pygame.display.Info().current_w - icon_size[0] - 15, 50)
                self.corruption_icon = CorruptionIcon(
                    manager=self.manager,
                    position=icon_position,
                    size=icon_size,
                    battle_hex_coords=battle.hex_coords,
                    corruption_powers=battle.corruption_powers
                )

    def create_context_buttons(self) -> None:
        """Create context-sensitive buttons based on selected hex."""
        # Clear existing buttons
        for button in self.context_buttons.values():
            button.kill()
        self.context_buttons.clear()

        if self.selected_hex is None:
            self.update_battle_info(None)
            return

        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
        is_upgrade_hex = upgrade_hexes.is_upgrade_hex(self.selected_hex)
        self.update_battle_info(battle)

        button_width = 120
        button_height = 40
        padding = 10
        bottom_margin = 10
        
        # Calculate starting position for buttons
        screen_rect = self.screen.get_rect()
        
        if battle is not None:
            # Three buttons for battle hexes
            total_width = (button_width * 3) + (padding * 2)
            start_x = (screen_rect.width - total_width) // 2
            y = screen_rect.height - bottom_margin - button_height

            self.context_buttons["edit"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x, y),
                    (button_width, button_height)
                ),
                text="Edit name/tip",
                manager=self.manager
            )
            
            self.context_buttons["sandbox"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x + button_width + padding, y),
                    (button_width, button_height)
                ),
                text="Edit in Sandbox",
                manager=self.manager
            )
            
            self.context_buttons["delete"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x + (button_width + padding) * 2, y),
                    (button_width, button_height)
                ),
                text="Delete",
                manager=self.manager
            )

            # Add corruption toggle button
            self.context_buttons["corruption"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x, y - button_height - padding),
                    (button_width, button_height)
                ),
                text="Toggle Corruption",
                manager=self.manager
            )
        elif is_upgrade_hex:
            # One button for upgrade hexes
            start_x = (screen_rect.width - button_width) // 2
            y = screen_rect.height - bottom_margin - button_height

            self.context_buttons["delete_upgrade"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x, y),
                    (button_width, button_height)
                ),
                text="Delete Upgrade",
                manager=self.manager
            )
        else:
            # Two buttons for empty hexes
            total_width = (button_width * 2) + padding
            start_x = (screen_rect.width - total_width) // 2
            y = screen_rect.height - bottom_margin - button_height

            self.context_buttons["create"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x, y),
                    (button_width, button_height)
                ),
                text="Create Battle",
                manager=self.manager
            )
            
            self.context_buttons["create_upgrade"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x + button_width + padding, y),
                    (button_width, button_height)
                ),
                text="Create Upgrade",
                manager=self.manager
            )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the world map scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            self.handle_escape(event)
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())
                    elif event.ui_element == self.context_buttons.get("sandbox"):
                        # Open the battle in sandbox mode
                        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
                        if battle:
                            pygame.event.post(
                                SetupBattleSceneEvent(
                                    current_scene_id=id(self),
                                    world_map_view=self.world_map_view,
                                    battle_id=battle.id,
                                    sandbox_mode=True,
                                    developer_mode=True,
                                    is_corrupted=battle.hex_coords in self.corrupted_hexes,
                                ).to_event()
                            )
                    elif event.ui_element == self.context_buttons.get("create"):
                        # Create a new battle at the selected hex
                        self.save_battle_dialog = SaveBattleDialog(
                            manager=self.manager,
                            ally_placements=None,
                            enemy_placements=[],  # Start with empty placements
                            existing_battle_id=None,
                            hex_coords=self.selected_hex,
                            show_test_button=False  # Only show save battle button
                        )
                    elif event.ui_element == self.context_buttons.get("create_upgrade"):
                        # Create a new upgrade hex at the selected hex
                        if self.selected_hex is not None:
                            # Add the upgrade hex and rebuild the view
                            upgrade_hexes.add_upgrade_hex(self.selected_hex)
                            self.world_map_view.rebuild(get_battles())
                            self.selected_hex = None
                            self.create_context_buttons()
                            self.create_statistics_display()
                    elif event.ui_element == self.context_buttons.get("edit"):
                        # Edit the selected battle's name and tip
                        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
                        if battle:
                            self.save_battle_dialog = SaveBattleDialog(
                                manager=self.manager,
                                ally_placements=battle.allies,
                                enemy_placements=battle.enemies,
                                existing_battle_id=battle.id,
                                hex_coords=battle.hex_coords,
                                show_test_button=False  # Only show save battle button
                            )
                    elif event.ui_element == self.context_buttons.get("delete"):
                        # Delete the selected battle
                        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
                        if battle:
                            battles.delete_battle(battle.id)
                            self.selected_hex = None
                            self.world_map_view.rebuild(get_battles())
                            self.create_context_buttons()
                            self.create_statistics_display()
                    elif event.ui_element == self.context_buttons.get("corruption"):
                        # Toggle corruption for the selected battle
                        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
                        if battle:
                            if battle.hex_coords in self.corrupted_hexes:
                                # Remove corruption
                                self.corrupted_hexes.remove(battle.hex_coords)
                            else:
                                # Add corruption
                                self.corrupted_hexes.append(battle.hex_coords)
                            self.create_context_buttons()
                            self.world_map_view.rebuild(get_battles())
                    elif event.ui_element == self.context_buttons.get("delete_upgrade"):
                        # Delete the selected upgrade hex
                        if self.selected_hex is not None and upgrade_hexes.is_upgrade_hex(self.selected_hex):
                            upgrade_hexes.remove_upgrade_hex(self.selected_hex)
                            self.selected_hex = None
                            self.world_map_view.rebuild(get_battles())
                            self.create_context_buttons()
                            self.create_statistics_display()
                    # Handle save battle dialog events
                    elif hasattr(self, 'save_battle_dialog'):
                        if event.ui_element == self.save_battle_dialog.save_battle_button:
                            self.save_battle_dialog.save_battle(is_test=False)
                            self.save_battle_dialog.kill()
                            delattr(self, 'save_battle_dialog')
                            self.world_map_view.rebuild(get_battles())
                            self.create_context_buttons()
                            self.create_statistics_display()
                        elif event.ui_element == self.save_battle_dialog.save_test_button:
                            self.save_battle_dialog.save_battle(is_test=True)
                            self.save_battle_dialog.kill()
                            delattr(self, 'save_battle_dialog')
                            self.world_map_view.rebuild(get_battles())
                            self.create_context_buttons()
                            self.create_statistics_display()
                        elif event.ui_element == self.save_battle_dialog.cancel_button:
                            self.save_battle_dialog.kill()
                            delattr(self, 'save_battle_dialog')

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                if not self.manager.get_hovering_any_element():
                    clicked_hex = self.world_map_view.get_hex_at_mouse_pos()
                    
                    # If clicking an empty hex while having a battle selected for moving
                    if (self.selected_hex is not None and 
                        self.world_map_view.get_battle_from_hex(self.selected_hex) is not None and
                        clicked_hex == self.move_target_hex and
                        not upgrade_hexes.is_upgrade_hex(clicked_hex)):
                        # Then move the battle to the clicked hex
                        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
                        updated_battle = battle.model_copy(update={'hex_coords': clicked_hex})
                        update_battle(battle, updated_battle)
                        self.world_map_view.rebuild(get_battles())
                        self.selected_hex = None
                        self.move_target_hex = None
                        self.create_context_buttons()
                    else:
                        # Select the clicked hex, whether it has a battle or not
                        self.selected_hex = clicked_hex
                        self.create_context_buttons()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
                self.selected_hex = None
                self.create_context_buttons()

            if event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT):
                # Don't process hex hovering if we're over a UI element
                if mouse_over_ui(self.manager):
                    self.hovered_hex = None
                    self.move_target_hex = None
                else:
                    hovered_hex = self.world_map_view.get_hex_at_mouse_pos()
                    self.hovered_hex = hovered_hex
                    self.move_target_hex = None

                    # Update battle info for hovered battle when no battle is selected
                    if self.selected_hex is None:
                        battle = self.world_map_view.get_battle_from_hex(hovered_hex)
                        self.update_battle_info(battle)

                    # When moving a battle, show the potential move target
                    if (
                        self.selected_hex is not None and 
                        self.world_map_view.get_battle_from_hex(self.selected_hex) is not None and 
                        self.world_map_view.get_battle_from_hex(hovered_hex) is None and
                        not upgrade_hexes.is_upgrade_hex(hovered_hex)
                    ):
                        self.move_target_hex = hovered_hex

            if not hasattr(self, 'save_battle_dialog'):
                self.world_map_view.camera.process_event(event)
            self.manager.process_events(event)

        states = defaultdict(HexState)
        for hex_coords in self.corrupted_hexes:
            states[hex_coords].border = BorderState.RED_BORDER
        if self.selected_hex is not None:
            states[self.selected_hex].border = BorderState.YELLOW_BORDER
        if self.move_target_hex is not None:
            states[self.move_target_hex].border = BorderState.GREEN_BORDER
        if self.hovered_hex is not None:
            states[self.hovered_hex].fill = FillState.HIGHLIGHTED
        self.world_map_view.reset_hex_states()
        self.world_map_view.update_hex_state(states)

        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        # Only update camera if no dialog is focused
        if not hasattr(self, 'save_battle_dialog'):
            self.world_map_view.camera.update(time_delta)
        self.world_map_view.draw_map()
        self.world_map_view.update_battles(time_delta)
        
        selected_unit_manager.update(time_delta)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)

    def _close_scene_windows(self) -> bool:
        """Close any open windows specific to the campaign editor scene."""
        windows_closed = False
        
        # Check for save battle dialog
        if hasattr(self, 'save_battle_dialog'):
            self.save_battle_dialog.kill()
            delattr(self, 'save_battle_dialog')
            windows_closed = True
            
        # Fall back to base class behavior and combine results
        return super()._close_scene_windows() or windows_closed
