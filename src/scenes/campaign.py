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
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event, PLAY_SOUND, PlaySoundEvent
from progress_manager import progress_manager
from scenes.events import PreviousSceneEvent, SetupBattleSceneEvent
from scenes.scene import Scene
from selected_unit_manager import selected_unit_manager
from ui_components.barracks_ui import BarracksUI
from ui_components.return_button import ReturnButton
from ui_components.feedback_button import FeedbackButton
from ui_components.corruption_panel import CorruptionPanel
from ui_components.corruption_congratulations_panel import CorruptionCongratulationsPanel
from world_map_view import BorderState, FillState, WorldMapView, HexState
from scene_utils import use_world
from ui_components.progress_panel import ProgressPanel
from ui_components.congratulations_panel import CongratulationsPanel
from ui_components.corruption_icon import CorruptionIcon
from ui_components.unit_tier_upgrade_ui import UnitTierUpgradeUI

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
        self.hovered_battle_hex: Optional[Tuple[int, int]] = None
        self.selected_battle_hex: Optional[Tuple[int, int]] = None
        
        # Store context buttons
        self.context_buttons: dict[str, pygame_gui.elements.UIButton] = {}

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
                    (pygame.display.Info().current_w - 295, barracks_bottom - 100),
                    (215, 100)
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
        self.unit_tier_upgrade_ui = None
        self.check_panels()
        self.create_ui()
        
    
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
        
        # Add unit tier upgrade button
        self.upgrade_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 10), (150, 40)),
            text="Unit Upgrades",
            manager=self.manager
        )
    def create_context_buttons(self) -> None:
        """Create context-sensitive buttons based on selected hex."""
        # Clear existing buttons
        for button in self.context_buttons.values():
            button.kill()
        self.context_buttons.clear()

        if self.corruption_icon is not None:
            self.corruption_icon.kill()
            self.corruption_icon = None

        if self.selected_battle_hex is None:
            return

        battle = self.world_map_view.get_battle_from_hex(self.selected_battle_hex)
        if battle is None:
            return

        if battle.hex_coords in self.world_map_view.corrupted_hexes:
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
            
            # Handle unit tier upgrade UI if it exists
            if self.unit_tier_upgrade_ui is not None:
                if self.unit_tier_upgrade_ui.handle_event(event):
                    # UI was closed
                    self.unit_tier_upgrade_ui = None
                continue

            # Handle congratulations panel events first if it exists
            if self.congratulations_panel is not None and self.congratulations_panel.handle_event(event):
                self.check_panels()
                continue
                
            # Handle corruption master panel events if it exists
            if self.corruption_congratulations_panel is not None and self.corruption_congratulations_panel.handle_event(event):
                self.check_panels()
                continue

            self.handle_escape(event)

            # Add enter key handling
            if (event.type == pygame.KEYDOWN and 
                event.key == pygame.K_RETURN and 
                self.selected_battle_hex is not None):
                # Simulate clicking the battle/improve button
                button = (self.context_buttons.get("battle") or 
                         self.context_buttons.get("improve"))
                if button is not None:
                    pygame.event.post(pygame.event.Event(
                        pygame.USEREVENT,
                        {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': button}
                    ))

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent().to_event())
                    elif event.ui_element == self.upgrade_button:
                        if self.unit_tier_upgrade_ui is None:
                            self.unit_tier_upgrade_ui = UnitTierUpgradeUI(self.screen, self.manager)
                    elif event.ui_element in (
                        self.context_buttons.get("battle"),
                        self.context_buttons.get("improve")
                    ):
                        battle = self.world_map_view.get_battle_from_hex(self.selected_battle_hex)
                        pygame.event.post(
                            SetupBattleSceneEvent(
                                world_map_view=self.world_map_view,
                                battle_id=battle.id,
                                sandbox_mode=False,
                                developer_mode=False,
                            ).to_event()
                        )

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                # Only process clicks if not over UI elements
                if not self.manager.get_hovering_any_element():
                    clicked_hex = self.world_map_view.get_hex_at_mouse_pos()
                    battle = self.world_map_view.get_battle_from_hex(clicked_hex)

                    # Only select if clicking an available battle hex
                    if (battle is not None and 
                        clicked_hex in progress_manager.available_battles()):
                        # If clicking the same hex that's already selected, trigger the button
                        if clicked_hex == self.selected_battle_hex:
                            button = (self.context_buttons.get("battle") or 
                                    self.context_buttons.get("improve"))
                            if button is not None:
                                pygame.event.post(pygame.event.Event(
                                    pygame.USEREVENT,
                                    {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': button}
                                ))
                        else:
                            self.selected_battle_hex = clicked_hex
                            self.create_context_buttons()
                            # Update grades panel with selected battle
                            if self.progress_panel is not None:
                                self.progress_panel.update_battle(battle)
                    else:
                        self.selected_battle_hex = None
                        self.create_context_buttons()
                        # Update grades panel with no battle
                        if self.progress_panel is not None:
                            self.progress_panel.update_battle(None)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
                self.selected_battle_hex = None
                self.create_context_buttons()
                # Update grades panel with no battle
                if self.progress_panel is not None:
                    self.progress_panel.update_battle(None)

            if event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT):
                # Don't process hex hovering if we're over a UI element
                if self.manager.get_hovering_any_element():
                    self.hovered_battle_hex = None
                    # If no selected battle, update grades panel to show no battle
                    if self.progress_panel is not None and self.selected_battle_hex is None:
                        self.progress_panel.update_battle(None)
                else:
                    hovered_hex = self.world_map_view.get_hex_at_mouse_pos()
                    old_hovered_hex = self.hovered_battle_hex
                    self.hovered_battle_hex = None
                    
                    # Only hover available battle hexes that aren't selected
                    if (
                        self.world_map_view.get_battle_from_hex(hovered_hex) is not None and
                        hovered_hex in progress_manager.available_battles()
                    ):
                        self.hovered_battle_hex = hovered_hex
                        
                    # Update grades panel if hover state changed and no battle is selected
                    if (self.progress_panel is not None and 
                        self.selected_battle_hex is None and 
                        old_hovered_hex != self.hovered_battle_hex):
                        if self.hovered_battle_hex is not None:
                            battle = self.world_map_view.get_battle_from_hex(self.hovered_battle_hex)
                            self.progress_panel.update_battle(battle)
                        else:
                            self.progress_panel.update_battle(None)

            self.world_map_view.camera.process_event(event)
            self.manager.process_events(event)
            self.feedback_button.handle_event(event)
            if self.barracks is not None:
                self.barracks.handle_event(event)
        # Update hex states while preserving fog of war
        available_battles = progress_manager.available_battles()
        states = defaultdict(HexState)
        for battle in get_battles():
            if battle.hex_coords is not None:
                # Mark corrupted battles with appropriate border color
                if progress_manager.is_battle_corrupted(battle.hex_coords):
                    if battle.hex_coords in progress_manager.solutions:
                        solution = progress_manager.solutions[battle.hex_coords]
                        if solution.solved_corrupted:
                            # Dark red border for corrupted battles that have been beaten in their corrupted state
                            states[battle.hex_coords].border = BorderState.DARK_RED_BORDER
                        else:
                            # Red border for corrupted battles that haven't been beaten in their corrupted state
                            states[battle.hex_coords].border = BorderState.RED_BORDER
                    else:
                        # Red border for corrupted battles that haven't been beaten yet
                        states[battle.hex_coords].border = BorderState.RED_BORDER
                
                if battle.hex_coords in available_battles:
                    # Mark available battles with green border if not yet solved
                    if battle.hex_coords not in progress_manager.solutions:
                        states[battle.hex_coords].fill = FillState.UNFOCUSED
                else:
                    states[battle.hex_coords].fill = FillState.FOGGED

        if self.selected_battle_hex is not None:
            states[self.selected_battle_hex].border = BorderState.YELLOW_BORDER
        if self.hovered_battle_hex is not None:
            states[self.hovered_battle_hex].fill = FillState.HIGHLIGHTED
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
                if battle.hex_coords is not None and battle.hex_coords in available_battles:
                    with use_world(battle.id):
                        for ent, (pos, unit_type, team, hitbox) in esper.get_components(Position, UnitTypeComponent, Team, Hitbox):
                            if unit_type.type == selected_unit_manager.selected_unit_type:
                                radius = (hitbox.width ** 2 + hitbox.height ** 2) ** 0.5
                                screen_pos = self.world_map_view.camera.world_to_screen(pos.x, pos.y)
                                color = gc.TEAM1_COLOR if team.type == TeamType.TEAM1 else gc.TEAM2_COLOR
                                pygame.draw.circle(self.screen, color, screen_pos, radius * self.world_map_view.camera.scale, width=1)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)
