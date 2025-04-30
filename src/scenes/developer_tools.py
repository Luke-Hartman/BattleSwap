from typing import List
import pygame
import pygame_gui
from camera import Camera
import battles
from scenes.scene import Scene
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scenes.events import (
    CampaignEditorSceneEvent,
    TestEditorSceneEvent,
    SetupBattleSceneEvent,
    PreviousSceneEvent,
)
from ui_components.return_button import ReturnButton
from world_map_view import WorldMapView
from game_constants import gc

class DeveloperToolsScene(Scene):
    """Scene containing developer tools and utilities."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager):
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.create_buttons()

    def create_buttons(self) -> None:
        button_width = 300
        button_height = 80
        button_spacing = 20
        
        # Calculate total height of all buttons including spacing
        total_buttons_height = 3 * button_height + 2 * button_spacing
        
        # Calculate starting Y position to center the buttons vertically
        screen_height = pygame.display.Info().current_h
        start_y = (screen_height - total_buttons_height) // 2
        
        # Calculate X position to center buttons horizontally
        screen_width = pygame.display.Info().current_w
        button_x = (screen_width - button_width) // 2

        # Create title
        title_width = 400
        title_height = 100
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (screen_width/2 - title_width/2, start_y - title_height - button_spacing),
                (title_width, title_height)
            ),
            text="Developer Tools",
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        self.return_button = ReturnButton(self.manager)

        # Create developer tools buttons
        self.campaign_editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y),
                (button_width, button_height)
            ),
            text="Campaign Editor",
            manager=self.manager
        )

        self.test_editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y + button_height + button_spacing),
                (button_width, button_height)
            ),
            text="Test Editor",
            manager=self.manager
        )

        self.sandbox_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y + 2 * (button_height + button_spacing)),
                (button_width, button_height)
            ),
            text="Developer Sandbox",
            manager=self.manager
        )

    def update(self, time_delta: float, events: List[pygame.event.Event]) -> bool:
        """Update the developer tools scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            self.handle_escape(event)
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.campaign_editor_button:
                        camera = Camera(zoom=1/2)
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=battles.get_battles(),
                            camera=camera,
                            corrupted_hexes=[],
                        )
                        pygame.event.post(CampaignEditorSceneEvent(
                            world_map_view=world_map_view,
                        ).to_event())
                    
                    elif event.ui_element == self.test_editor_button:
                        pygame.event.post(TestEditorSceneEvent().to_event())
                    
                    elif event.ui_element == self.sandbox_button:
                        battle = battles.Battle(
                            id="sandbox",
                            tip=["A customizable battle for experimenting"],
                            hex_coords=(0, 0),
                            allies=[],
                            enemies=[],
                            is_test=False,
                        )

                        camera = Camera()
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=[battle],
                            camera=camera,
                            corrupted_hexes=[],
                        )
                        pygame.event.post(SetupBattleSceneEvent(
                            world_map_view=world_map_view,
                            battle_id=battle.id,
                            sandbox_mode=True,
                            developer_mode=True,
                        ).to_event())
                    
                    elif event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent().to_event())

            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        self.manager.draw_ui(self.screen)
        return True
