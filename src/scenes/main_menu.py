from typing import List
import pygame
import pygame_gui
from camera import Camera
from scenes.scene import Scene
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scenes.events import SettingsSceneEvent, SetupBattleSceneEvent, CampaignSceneEvent, DeveloperToolsSceneEvent
from world_map_view import WorldMapView
from progress_manager import progress_manager, reset_progress

class MainMenuScene(Scene):
    """Main menu scene with primary navigation options for the game."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager):
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.confirmation_dialog: pygame_gui.elements.UIConfirmationDialog | None = None
        self.create_buttons()

    def create_buttons(self) -> None:
        button_width = 300
        button_height = 80
        button_spacing = 20
        
        # Calculate total height of all buttons including spacing
        total_buttons_height = 5 * button_height + 4 * button_spacing
        
        # Calculate starting Y position to center the buttons vertically
        screen_height = pygame.display.Info().current_h
        start_y = (screen_height - total_buttons_height) // 2
        
        # Calculate X position to center buttons horizontally
        screen_width = pygame.display.Info().current_w
        button_x = (screen_width - button_width) // 2

        # Create reset progress button in top right corner
        reset_button_width = 150
        reset_button_height = 40
        margin = 20
        self.reset_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (screen_width - reset_button_width - margin, margin),
                (reset_button_width, reset_button_height)
            ),
            text="Reset Progress",
            manager=self.manager
        )

        # Create title
        title_height = 100
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (screen_width/2 - button_width/2, start_y - title_height - button_spacing),
                (button_width, title_height)
            ),
            text="BattleSwap",
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        # Create main menu buttons
        self.campaign_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y),
                (button_width, button_height)
            ),
            text="Play Campaign",
            manager=self.manager
        )

        self.sandbox_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y + button_height + button_spacing),
                (button_width, button_height)
            ),
            text="Sandbox Mode",
            manager=self.manager
        )

        self.settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y + 2 * (button_height + button_spacing)),
                (button_width, button_height)
            ),
            text="Settings",
            manager=self.manager
        )

        self.developer_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y + 3 * (button_height + button_spacing)),
                (button_width, button_height)
            ),
            text="Developer Tools",
            manager=self.manager
        )

        self.exit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, start_y + 4 * (button_height + button_spacing)),
                (button_width, button_height)
            ),
            text="Exit",
            manager=self.manager
        )

    def update(self, time_delta: float, events: List[pygame.event.Event]) -> bool:
        """Update the main menu scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.campaign_button:
                        camera = Camera(zoom=1/2)
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=progress_manager.get_battles_including_solutions(),
                            camera=camera
                        )
                        pygame.event.post(CampaignSceneEvent(
                            world_map_view=world_map_view,
                        ).to_event())
                    
                    elif event.ui_element == self.sandbox_button:
                        pygame.event.post(SetupBattleSceneEvent(
                            world_map_view=None,
                            battle_id=None,
                            sandbox_mode=True,
                            developer_mode=False,
                        ).to_event())
                    
                    elif event.ui_element == self.settings_button:
                        pygame.event.post(SettingsSceneEvent().to_event())

                    elif event.ui_element == self.developer_button:
                        pygame.event.post(DeveloperToolsSceneEvent().to_event())
                    
                    elif event.ui_element == self.exit_button:
                        return False
                    
                    elif event.ui_element == self.reset_button:
                        self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
                            rect=pygame.Rect((pygame.display.Info().current_w/2 - 150, pygame.display.Info().current_h/2 - 100), (300, 200)),
                            manager=self.manager,
                            window_title="Reset Progress",
                            action_long_desc="Are you sure you want to reset all game progress? This cannot be undone.",
                            action_short_name="Reset",
                            blocking=True
                        )

                elif event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if self.confirmation_dialog is not None and event.ui_element == self.confirmation_dialog:
                        reset_progress()
                        print(progress_manager.solutions)
                        self.confirmation_dialog = None

            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return True
