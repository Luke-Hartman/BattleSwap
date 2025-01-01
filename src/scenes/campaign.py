from collections import defaultdict
from game_constants import gc
from typing import Tuple, Optional

import pygame
import pygame_gui

from battles import get_battles
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from progress_manager import ProgressManager
from scenes.events import PreviousSceneEvent, SandboxSceneEvent
from scenes.scene import Scene
from camera import Camera
from ui_components.barracks_ui import BarracksUI
from ui_components.return_button import ReturnButton
from world_map_view import BorderState, FillState, WorldMapView, HexState

class CampaignScene(Scene):
    """A 2D hex grid world map for progressing through the campaign."""
    
    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        world_map_view: WorldMapView,
        progress_manager: ProgressManager
    ) -> None:
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.progress_manager = progress_manager
        self.world_map_view = world_map_view

        # Create camera with desired initial settings
        self.hovered_battle_hex: Optional[Tuple[int, int]] = None
        self.selected_battle_hex: Optional[Tuple[int, int]] = None
        
        # Store context buttons
        self.context_buttons: dict[str, pygame_gui.elements.UIButton] = {}

        if self.progress_manager.solutions:
            self.barracks = BarracksUI(
                self.manager,
                self.progress_manager.available_units(None),
                interactive=False,
                sandbox_mode=False,
            )
        else:
            self.barracks = None
        
        self.create_ui()

    def create_ui(self) -> None:
        """Create the UI elements for the world map scene."""
        self.return_button = ReturnButton(self.manager)

    def create_context_buttons(self) -> None:
        """Create context-sensitive buttons based on selected hex."""
        # Clear existing buttons
        for button in self.context_buttons.values():
            button.kill()
        self.context_buttons.clear()

        if self.selected_battle_hex is None:
            return

        battle = self.world_map_view.get_battle_from_hex(self.selected_battle_hex)
        if battle is None:
            return

        button_width = 120
        button_height = 40
        bottom_margin = 20 + 84 if self.barracks is not None else 20
        
        # Calculate position for single centered button
        screen_rect = self.screen.get_rect()
        start_x = (screen_rect.width - button_width) // 2
        y = screen_rect.height - bottom_margin - button_height

        # Show different button based on whether battle is solved
        if battle.hex_coords in self.progress_manager.solutions:
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
            
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.return_button:
                    pygame.event.post(PreviousSceneEvent().to_event())
                elif event.ui_element in (
                    self.context_buttons.get("battle"),
                    self.context_buttons.get("improve")
                ):
                    battle = self.world_map_view.get_battle_from_hex(self.selected_battle_hex)
                    pygame.event.post(
                        SandboxSceneEvent(
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
                        clicked_hex in self.progress_manager.available_battles()):
                        self.selected_battle_hex = clicked_hex
                        self.create_context_buttons()
                    else:
                        self.selected_battle_hex = None
                        self.create_context_buttons()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT:
                self.selected_battle_hex = None
                self.create_context_buttons()

            if event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT):
                # Don't process hex hovering if we're over a UI element
                if self.manager.get_hovering_any_element():
                    self.hovered_battle_hex = None
                else:
                    hovered_hex = self.world_map_view.get_hex_at_mouse_pos()
                    self.hovered_battle_hex = None
                    
                    # Only hover available battle hexes that aren't selected
                    if (
                        self.world_map_view.get_battle_from_hex(hovered_hex) is not None and
                        hovered_hex in self.progress_manager.available_battles()
                    ):
                        self.hovered_battle_hex = hovered_hex

            self.world_map_view.camera.process_event(event)
            self.manager.process_events(event)

        # Update hex states while preserving fog of war
        available_battles = self.progress_manager.available_battles()
        states = defaultdict(HexState)
        for battle in get_battles():
            if battle.hex_coords is not None:
                if battle.hex_coords in available_battles:
                    # Mark available battles with green border if not yet solved
                    if battle.hex_coords not in self.progress_manager.solutions:
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
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)
