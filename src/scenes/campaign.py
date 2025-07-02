from collections import defaultdict
from game_constants import gc
from typing import Tuple, Optional, List

import pygame
import pygame_gui
import esper

from battles import get_battles
from components.hitbox import Hitbox
from components.position import Position
from components.team import Team, TeamType
from components.unit_type import UnitTypeComponent
from components.unit_tier import UnitTier
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event, PLAY_SOUND, PlaySoundEvent
from progress_manager import progress_manager, HexLifecycleState
from scenes.events import PreviousSceneEvent, SetupBattleSceneEvent
from scenes.scene import Scene
from selected_unit_manager import selected_unit_manager
from ui_components.barracks_ui import BarracksUI
from ui_components.return_button import ReturnButton
from ui_components.feedback_button import FeedbackButton
from ui_components.corruption_panel import CorruptionPanel
from ui_components.corruption_congratulations_panel import CorruptionCongratulationsPanel
from ui_components.upgrade_window import UpgradeWindow
from world_map_view import BorderState, FillState, WorldMapView, HexState
from scene_utils import use_world
from ui_components.progress_panel import ProgressPanel
from ui_components.congratulations_panel import CongratulationsPanel
from ui_components.corruption_icon import CorruptionIcon
import upgrade_hexes

class CampaignScene(Scene):
    """A 2D hex grid world map for progressing through the campaign."""
    
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
        self.corruption_dialog = None
        self.corrupted_battles = None
        self.corruption_icon = None

        # Create camera with desired initial settings
        self.hovered_hex: Optional[Tuple[int, int]] = None
        self.selected_hex: Optional[Tuple[int, int]] = None
        
        # Store context buttons
        self.context_buttons: dict[str, pygame_gui.elements.UIButton] = {}

        # Flash animation state for upgrade button
        self.upgrade_button_flash_time = 0.0
        self.upgrade_button_flash_duration = 1.0  # Total flash duration in seconds
        self.upgrade_button_flash_alternations = 6  # Number of border switches (3 full cycles)
        self.upgrade_button_flash_interval = self.upgrade_button_flash_duration / self.upgrade_button_flash_alternations
        self.upgrade_button_is_flashing = False
        self.upgrade_button_flash_state = False  # False = normal, True = flash theme

        if progress_manager.solutions:
            self.barracks = BarracksUI(
                self.manager,
                progress_manager.available_units(None),
                interactive=True,
                sandbox_mode=False,
                current_battle=None,
            )
            # Create grades panel to the right of barracks, aligned at the bottom
            barracks_bottom = self.barracks.rect.bottom
            self.progress_panel = ProgressPanel(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 295, barracks_bottom - 108),
                    (235, 115)
                ),
                manager=self.manager,
                current_battle=None
            )
        else:
            self.barracks = None
            self.progress_panel = None
        
        self.congratulations_panel = None
        self.corruption_congratulations_panel = None
        self.corruption_dialog = None
        self.upgrade_window = None
        self.check_panels()
        self.create_ui()
        
    def _has_claimed_upgrade_hexes(self) -> bool:
        """Check if the player has any claimed upgrade hexes."""
        for coords, state in progress_manager.hex_states.items():
            if (upgrade_hexes.is_upgrade_hex(coords) and 
                state in [HexLifecycleState.CLAIMED, HexLifecycleState.CORRUPTED,HexLifecycleState.RECLAIMED]):
                return True
        return False
    
    def _all_units_are_basic(self) -> bool:
        """Check if all units are still at basic tier."""
        if not progress_manager.unit_tiers:
            return True
        return all(tier == UnitTier.BASIC for tier in progress_manager.unit_tiers.values())
    
    def _should_upgrade_button_flash(self) -> bool:
        """Check if the upgrade button should flash (has claimed upgrade hexes but all units are basic)."""
        return (self._has_claimed_upgrade_hexes() and 
                self._all_units_are_basic() and 
                self.upgrade_window is None)
    
    def _update_upgrade_button_flash_theme(self):
        """Update the upgrade button theme based on flash state."""
        if self.upgrade_button.alive():
            if self.upgrade_button_flash_state:
                # Switch to flash theme
                self.upgrade_button.change_object_id(pygame_gui.core.ObjectID(object_id='#flash_button'))
            else:
                # Switch back to normal theme
                self.upgrade_button.change_object_id(pygame_gui.core.ObjectID(class_id='button'))
    
    def _update_upgrade_button_state(self):
        """Update the upgrade button enabled/disabled state and flashing."""
        has_claimed_hexes = self._has_claimed_upgrade_hexes()
        should_flash = self._should_upgrade_button_flash()
        
        # Enable/disable button
        if has_claimed_hexes:
            self.upgrade_button.enable()
        else:
            self.upgrade_button.disable()
        
        # Start/stop flashing
        if should_flash and not self.upgrade_button_is_flashing:
            self.upgrade_button_is_flashing = True
            self.upgrade_button_flash_time = 0.0
            self.upgrade_button_flash_state = False
        elif not should_flash and self.upgrade_button_is_flashing:
            self.upgrade_button_is_flashing = False
            self.upgrade_button_flash_time = 0.0
            self.upgrade_button_flash_state = False
            self._update_upgrade_button_flash_theme()  # Ensure we end on normal theme
    
    def check_panels(self) -> None:
        # Check if we should show congratulations
        if progress_manager.should_show_congratulations():
            self.congratulations_panel = CongratulationsPanel(
                manager=self.manager,
            )
            return
        else:
            self.congratulations_panel = None
            
        # Check if we should show corruption congratulations
        if progress_manager.should_show_corruption_congratulations():
            self.corruption_congratulations_panel = CorruptionCongratulationsPanel(
                manager=self.manager,
            )
            return
        else:
            self.corruption_congratulations_panel = None

        if progress_manager.should_trigger_corruption():
            corrupted_battles = progress_manager.corrupt_battles()
            if corrupted_battles:
                self.corruption_dialog = CorruptionPanel(
                    manager=self.manager,
                    corrupted_battles=corrupted_battles,
                    world_map_view=self.world_map_view
                )
                self.corrupted_battles = corrupted_battles

    def create_ui(self) -> None:
        """Create the UI elements for the world map scene."""
        self.return_button = ReturnButton(self.manager)
        self.feedback_button = FeedbackButton(self.manager)
        
        # Create upgrade button in top right
        button_width = 120
        button_height = 40
        screen_rect = self.screen.get_rect()
        upgrade_button_x = screen_rect.width - button_width - 20
        upgrade_button_y = 20
        
        self.upgrade_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(upgrade_button_x, upgrade_button_y, button_width, button_height),
            text="Upgrade Units",
            manager=self.manager
        )
        
        # Set initial button state
        self._update_upgrade_button_state()

    def create_context_buttons(self) -> None:
        """Create context-sensitive buttons based on selected hex."""
        # Clear existing buttons
        for button in self.context_buttons.values():
            button.kill()
        self.context_buttons.clear()

        if self.corruption_icon is not None:
            self.corruption_icon.kill()
            self.corruption_icon = None

        if self.selected_hex is None:
            return

        # Check if this is a battle hex
        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
        is_upgrade_hex = upgrade_hexes.is_upgrade_hex(self.selected_hex)
        
        if battle is None and not is_upgrade_hex:
            return

        # Show corruption icon for corrupted battles
        if battle is not None and progress_manager.get_hex_state(battle.hex_coords) in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]:
            icon_size = (48, 48)
            icon_position = (pygame.display.Info().current_w - icon_size[0] - 15, 50)
            self.corruption_icon = CorruptionIcon(
                manager=self.manager,
                position=icon_position,
                size=icon_size,
                battle_hex_coords=battle.hex_coords,
                corruption_powers=battle.corruption_powers
            )

        button_width = 120
        button_height = 40
        bottom_margin = 20 + (self.barracks.rect.height - 25) if self.barracks is not None else 20
        
        # Calculate position for single centered button
        screen_rect = self.screen.get_rect()
        start_x = (screen_rect.width - button_width) // 2
        y = screen_rect.height - bottom_margin - button_height

        if is_upgrade_hex:
            # Show claim button for upgrade hexes
            hex_state = progress_manager.get_hex_state(self.selected_hex)
            is_claimable = hex_state in [HexLifecycleState.UNCLAIMED, HexLifecycleState.CORRUPTED]
            
            # Determine button text based on hex state
            if hex_state == HexLifecycleState.FOGGED:
                button_text = "Explore more"
            elif hex_state == HexLifecycleState.UNCLAIMED:
                button_text = "Claim"
            elif hex_state == HexLifecycleState.CLAIMED:
                button_text = "Claimed"
            elif hex_state == HexLifecycleState.CORRUPTED:
                button_text = "Reclaim"
            elif hex_state == HexLifecycleState.RECLAIMED:
                button_text = "Reclaimed"
            else:
                button_text = "Claim"
            
            self.context_buttons["claim"] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (start_x, y),
                    (button_width, button_height)
                ),
                text=button_text,
                manager=self.manager
            )
            
            # Disable button if not claimable
            if not is_claimable:
                self.context_buttons["claim"].disable()
                if hex_state == HexLifecycleState.FOGGED:
                    self.context_buttons["claim"].tool_tip_text = "Claim adjacent hexes to unlock this upgrade hex"
                elif hex_state == HexLifecycleState.CLAIMED:
                    self.context_buttons["claim"].tool_tip_text = "This upgrade hex has been claimed (wait for corruption)"
                elif hex_state == HexLifecycleState.RECLAIMED:
                    self.context_buttons["claim"].tool_tip_text = "This upgrade hex has been fully reclaimed"
        
        elif battle is not None:
            # Show different button based on whether battle is solved
            if battle.hex_coords in progress_manager.solutions:
                self.context_buttons["improve"] = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(
                        (start_x, y),
                        (button_width, button_height)
                    ),
                    text="Improve",
                    manager=self.manager
                )
            else:
                self.context_buttons["battle"] = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(
                        (start_x, y),
                        (button_width, button_height)
                    ),
                    text="Battle",
                    manager=self.manager
                )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the world map scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False

            # Handle corruption dialog if it exists
            if self.corruption_dialog is not None and self.corruption_dialog.handle_event(event):
                self.corruption_dialog = None
                
                # If we have corrupted battles, hover over the first one
                if self.corrupted_battles and len(self.corrupted_battles) > 0:
                    battle = self.world_map_view.get_battle_from_hex(self.corrupted_battles[0])
                    self.world_map_view.move_camera_above_battle(battle.id)
                continue

            # Handle congratulations panel events first if it exists
            if self.congratulations_panel is not None and self.congratulations_panel.handle_event(event):
                self.check_panels()
                continue
                
            # Handle corruption master panel events if it exists
            if self.corruption_congratulations_panel is not None and self.corruption_congratulations_panel.handle_event(event):
                self.check_panels()
                continue

            # Handle upgrade window events if it exists
            if self.upgrade_window is not None and self.upgrade_window.handle_event(event):
                continue

            self.handle_escape(event)

            # Add enter key handling
            if (event.type == pygame.KEYDOWN and 
                event.key == pygame.K_RETURN and 
                self.selected_hex is not None):
                # Simulate clicking the appropriate button
                button = (self.context_buttons.get("battle") or 
                         self.context_buttons.get("improve") or
                         self.context_buttons.get("claim"))
                if button is not None:
                    pygame.event.post(pygame.event.Event(
                        pygame.USEREVENT,
                        {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': button}
                    ))

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())
                    elif event.ui_element == self.upgrade_button:
                        # Create a new upgrade window each time
                        if self.upgrade_window is not None:
                            self.upgrade_window.kill()
                        self.upgrade_window = UpgradeWindow(self.manager)
                        # Update button state in case units were upgraded
                        self._update_upgrade_button_state()
                    elif event.ui_element in (
                        self.context_buttons.get("battle"),
                        self.context_buttons.get("improve")
                    ):
                        battle = self.world_map_view.get_battle_from_hex(self.selected_hex)
                        pygame.event.post(
                            SetupBattleSceneEvent(
                                current_scene_id=id(self),
                                world_map_view=self.world_map_view,
                                battle_id=battle.id,
                                sandbox_mode=False,
                                developer_mode=False,
                                is_corrupted=progress_manager.get_hex_state(battle.hex_coords) in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED],
                            ).to_event()
                        )
                    elif event.ui_element == self.context_buttons.get("claim"):
                        # Handle upgrade hex claiming
                        if self.selected_hex is not None and upgrade_hexes.is_upgrade_hex(self.selected_hex):
                            progress_manager.claim_hex(self.selected_hex)
                            self.create_context_buttons()
                            self._update_upgrade_button_state()  # Update upgrade button state
                            emit_event(PLAY_SOUND, event=PlaySoundEvent(filename="unit_picked_up.wav", volume=1.0))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                # Only process clicks if not over UI elements
                if not self.manager.get_hovering_any_element():
                    clicked_hex = self.world_map_view.get_hex_at_mouse_pos()
                    battle = self.world_map_view.get_battle_from_hex(clicked_hex)

                    # Select if clicking an available battle hex or accessible upgrade hex
                    hex_state = progress_manager.get_hex_state(clicked_hex)
                    can_select = hex_state is not None and hex_state != HexLifecycleState.FOGGED
                    
                    if can_select:
                        # If clicking the same hex that's already selected, trigger the button
                        if clicked_hex == self.selected_hex:
                            button = (self.context_buttons.get("battle") or 
                                    self.context_buttons.get("improve") or
                                    self.context_buttons.get("claim"))
                            if button is not None:
                                pygame.event.post(pygame.event.Event(
                                    pygame.USEREVENT,
                                    {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': button}
                                ))
                        else:
                            self.selected_hex = clicked_hex
                            self.create_context_buttons()
                            # Update grades panel with selected battle (if it's a battle)
                            if self.progress_panel is not None:
                                self.progress_panel.update_battle(battle)
                    else:
                        self.selected_hex = None
                        self.create_context_buttons()
                        # Update grades panel with no battle
                        if self.progress_panel is not None:
                            self.progress_panel.update_battle(None)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
                self.selected_hex = None
                self.create_context_buttons()
                # Update grades panel with no battle
                if self.progress_panel is not None:
                    self.progress_panel.update_battle(None)

            if event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT):
                # Don't process hex hovering if we're over a UI element
                if self.manager.get_hovering_any_element():
                    self.hovered_hex = None
                    # If no selected hex, update grades panel to show no battle
                    if self.progress_panel is not None and self.selected_hex is None:
                        self.progress_panel.update_battle(None)
                else:
                    hovered_hex = self.world_map_view.get_hex_at_mouse_pos()
                    old_hovered_hex = self.hovered_hex
                    self.hovered_hex = None
                    
                    # Hover available battle hexes or accessible upgrade hexes that aren't selected
                    
                    hex_state = progress_manager.get_hex_state(hovered_hex)
                    can_hover = hex_state is not None and hex_state != HexLifecycleState.FOGGED
                    
                    if can_hover:
                        self.hovered_hex = hovered_hex
                        
                    # Update grades panel if hover state changed and no hex is selected
                    if (self.progress_panel is not None and 
                        self.selected_hex is None and 
                        old_hovered_hex != self.hovered_hex):
                        if self.hovered_hex is not None:
                            battle = self.world_map_view.get_battle_from_hex(self.hovered_hex)
                            self.progress_panel.update_battle(battle)
                        else:
                            self.progress_panel.update_battle(None)

            self.world_map_view.camera.process_event(event)
            self.manager.process_events(event)
            self.feedback_button.handle_event(event)
            if self.barracks is not None:
                self.barracks.handle_event(event)
        # Update hex states while preserving fog of war
        states = defaultdict(HexState)
        for hex_coords, state in progress_manager.hex_states.items():
            if progress_manager.get_hex_state(hex_coords) == HexLifecycleState.CORRUPTED:
                states[hex_coords].border = BorderState.RED_BORDER
            elif progress_manager.get_hex_state(hex_coords) == HexLifecycleState.RECLAIMED:
                states[hex_coords].border = BorderState.DARK_RED_BORDER
            elif state == HexLifecycleState.CLAIMED:
                states[hex_coords].fill = FillState.NORMAL
            elif state == HexLifecycleState.UNCLAIMED:
                states[hex_coords].fill = FillState.UNFOCUSED
            elif state == HexLifecycleState.FOGGED:
                states[hex_coords].fill = FillState.FOGGED

        if self.selected_hex is not None:
            states[self.selected_hex].border = BorderState.YELLOW_BORDER
        if self.hovered_hex is not None:
            states[self.hovered_hex].fill = FillState.HIGHLIGHTED
        self.world_map_view.reset_hex_states()
        self.world_map_view.update_hex_state(states)
        
        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        
        self.world_map_view.camera.update(time_delta)
        self.world_map_view.draw_map()
        self.world_map_view.update_battles(time_delta)
        selected_unit_manager.update(time_delta)

        # Draw circles around units if there is a selected unit type
        if selected_unit_manager.selected_unit_type is not None:
            for battle in get_battles():
                hex_state = progress_manager.get_hex_state(battle.hex_coords)
                if battle.hex_coords is not None and hex_state is not None and hex_state != HexLifecycleState.FOGGED:
                    with use_world(battle.id):
                        for ent, (pos, unit_type, team, hitbox) in esper.get_components(Position, UnitTypeComponent, Team, Hitbox):
                            if unit_type.type == selected_unit_manager.selected_unit_type:
                                radius = (hitbox.width ** 2 + hitbox.height ** 2) ** 0.5
                                screen_pos = self.world_map_view.camera.world_to_screen(pos.x, pos.y)
                                color = gc.TEAM1_COLOR if team.type == TeamType.TEAM1 else gc.TEAM2_COLOR
                                pygame.draw.circle(self.screen, color, screen_pos, radius * self.world_map_view.camera.scale, width=1)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)

        # Update upgrade window if it exists
        if self.upgrade_window is not None:
            self.upgrade_window.update(time_delta)

        # Update upgrade button state (check for changes in upgrade hexes or unit tiers)
        self._update_upgrade_button_state()
        
        # Update upgrade button flash animation
        if self.upgrade_button_is_flashing:
            self.upgrade_button_flash_time += time_delta
            
            # Calculate current alternation
            current_alternation = int(self.upgrade_button_flash_time / self.upgrade_button_flash_interval)
            new_flash_state = (current_alternation % 2) == 1
            
            # Update theme if state changed
            if new_flash_state != self.upgrade_button_flash_state:
                self.upgrade_button_flash_state = new_flash_state
                self._update_upgrade_button_flash_theme()
            
            # End flash after all alternations
            if self.upgrade_button_flash_time >= self.upgrade_button_flash_duration:
                self.upgrade_button_is_flashing = False
                self.upgrade_button_flash_time = 0.0
                self.upgrade_button_flash_state = False
                self._update_upgrade_button_flash_theme()  # Ensure we end on normal theme

        return super().update(time_delta, events)
