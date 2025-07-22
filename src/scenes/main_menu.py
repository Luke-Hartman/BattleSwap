from typing import List, Optional
import pygame
import pygame_gui
from camera import Camera
from keyboard_shortcuts import KeyboardShortcuts, format_button_text
from scenes.scene import Scene
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event, PLAY_SOUND, PlaySoundEvent
from scenes.events import SettingsSceneEvent, SetupBattleSceneEvent, CampaignSceneEvent, DeveloperToolsSceneEvent
from world_map_view import WorldMapView
from progress_manager import progress_manager, reset_progress, has_incompatible_save
from game_constants import gc
class MainMenuScene(Scene):
    """Main menu scene with primary navigation options for the game."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager, developer_mode: bool):
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.developer_mode = developer_mode
        self.confirmation_dialog: Optional[pygame_gui.windows.UIConfirmationDialog] = None
        self.create_buttons(developer_mode)
        
        # Check for incompatible save file
        if has_incompatible_save():
            self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
                rect=pygame.Rect((pygame.display.Info().current_w/2 - 200, pygame.display.Info().current_h/2 - 100), (400, 200)),
                manager=self.manager,
                window_title="Game Updated",
                action_long_desc="The game has had breaking changes and your saved progress is no longer compatible. You'll need to reset your progress. Sorry for the inconvenience!",
                action_short_name="Reset Progress",
                blocking=True
            )

    def create_buttons(self, developer_mode: bool) -> None:
        button_width = 300
        button_height = 80
        button_spacing = 20

        # Calculate total height of all buttons including spacing
        if developer_mode:
            total_buttons_height = 5 * button_height + 4 * button_spacing
        else:
            total_buttons_height = 4 * button_height + 3 * button_spacing

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
            text="Battle Swap",
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        # Create main menu buttons
        y = start_y
        self.campaign_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, y),
                (button_width, button_height)
            ),
            text=format_button_text("Play Campaign", KeyboardShortcuts.ENTER),
            manager=self.manager
        )
        y += button_height + button_spacing

        self.sandbox_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, y),
                (button_width, button_height)
            ),
            text="Sandbox Mode",
            manager=self.manager
        )
        y += button_height + button_spacing

        self.settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, y),
                (button_width, button_height)
            ),
            text="Settings",
            manager=self.manager
        )
        y += button_height + button_spacing
        if developer_mode:
            self.developer_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (button_x, y),
                    (button_width, button_height)
                ),
                text="Developer Tools",
                manager=self.manager
            )
            y += button_height + button_spacing
        else:
            self.developer_button = None

        self.exit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (button_x, y),
                (button_width, button_height)
            ),
            text=format_button_text("Exit", KeyboardShortcuts.ESCAPE),
            manager=self.manager
        )
        y += button_height + button_spacing

    def show_quit_confirmation(self) -> None:
        """Show confirmation dialog for quitting the game."""
        self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect((pygame.display.Info().current_w/2 - 150, pygame.display.Info().current_h/2 - 100), (300, 200)),
            manager=self.manager,
            window_title="Quit Game",
            action_long_desc="Are you sure you want to quit the game?",
            action_short_name=format_button_text("Quit", KeyboardShortcuts.ENTER),
            blocking=True
        )

    def handle_quit(self) -> bool:
        """Handle quit request from escape key or exit button."""
        if self.confirmation_dialog is None:
            self.show_quit_confirmation()
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.5
            ))
            return True
        return False

    def update(self, time_delta: float, events: List[pygame.event.Event]) -> bool:
        """Update the main menu scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if self.handle_confirmation_dialog_keys(event):
                continue
            
            if self.handle_confirmation_dialog_events(event):
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return self.handle_quit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                pygame.event.post(CampaignSceneEvent(
                    current_scene_id=id(self),
                ).to_event())
                
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.campaign_button:
                        pygame.event.post(CampaignSceneEvent(
                            current_scene_id=id(self),
                        ).to_event())
                    
                    elif event.ui_element == self.sandbox_button:
                        pygame.event.post(SetupBattleSceneEvent(
                            current_scene_id=id(self),
                            world_map_view=None,
                            battle_id=None,
                            sandbox_mode=True,
                            developer_mode=False,
                            is_corrupted=False,
                        ).to_event())
                    
                    elif event.ui_element == self.settings_button:
                        pygame.event.post(SettingsSceneEvent(current_scene_id=id(self)).to_event())

                    elif event.ui_element == self.developer_button:
                        pygame.event.post(DeveloperToolsSceneEvent(current_scene_id=id(self)).to_event())

                    elif event.ui_element == self.exit_button:
                        return self.handle_quit()
                    
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
                    if self.confirmation_dialog is not None:
                        if event.ui_element == self.confirmation_dialog:
                            if (self.confirmation_dialog.title_bar.text == "Reset Progress" or 
                                self.confirmation_dialog.title_bar.text == "Game Updated"):
                                reset_progress()
                            elif self.confirmation_dialog.title_bar.text == "Quit Game":
                                return False
                            self.confirmation_dialog = None

            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        self.manager.draw_ui(self.screen)
        return True
