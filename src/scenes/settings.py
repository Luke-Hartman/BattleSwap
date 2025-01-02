"""Settings scene for modifying user settings."""

import pygame
import pygame_gui
from typing import Dict

from events import CHANGE_MUSIC, CHANGE_MUSIC_VOLUME, ChangeMusicEvent, ChangeMusicVolumeEvent, emit_event
from scenes.events import PREVIOUS_SCENE_EVENT, PreviousSceneEvent
from scenes.scene import Scene
from settings import settings, save_settings
from ui_components.return_button import ReturnButton

class SettingsScene(Scene):
    """Scene for modifying user settings."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager):
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.sliders: Dict[str, pygame_gui.elements.UIHorizontalSlider] = {}
        self.create_ui()

    def create_ui(self) -> None:
        """Create the UI elements for the settings scene."""
        # Create return button
        self.return_button = ReturnButton(self.manager)

        # Create a panel to hold settings
        panel_width = 400
        panel_height = 230
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        settings_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=self.manager
        )

        # Title
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, 10),
                (panel_width - 20, 30)
            ),
            text="Settings",
            manager=self.manager,
            container=settings_panel
        )

        # Sound Settings
        y_offset = 50
        label_width = 150
        slider_width = 200
        element_height = 30
        padding = 10

        # Sound Volume
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (label_width, element_height)
            ),
            text="Sound Volume",
            manager=self.manager,
            container=settings_panel
        )

        self.sliders["SOUND_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.SOUND_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel
        )

        # Music Volume
        y_offset += element_height + padding
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (label_width, element_height)
            ),
            text="Music Volume",
            manager=self.manager,
            container=settings_panel
        )

        self.sliders["MUSIC_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.MUSIC_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel
        )

        # Voice Volume
        y_offset += element_height + padding
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (label_width, element_height)
            ),
            text="Voice Volume",
            manager=self.manager,
            container=settings_panel
        )

        self.sliders["VOICE_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.VOICE_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel
        )

        # Save Button
        y_offset += element_height + padding * 2
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                ((panel_width - 100) // 2, y_offset),
                (100, element_height)
            ),
            text="Save",
            manager=self.manager,
            container=settings_panel
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the settings scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.save_button:
                        # Update settings with current slider values
                        for setting_name, slider in self.sliders.items():
                            setattr(settings, setting_name, slider.get_current_value())
                        save_settings()
                        # Update music volume
                        emit_event(CHANGE_MUSIC_VOLUME, event=ChangeMusicVolumeEvent(
                            volume=settings.MUSIC_VOLUME,
                        ))
                    elif event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent().to_event())

            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events) 