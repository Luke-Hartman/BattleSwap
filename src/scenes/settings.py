"""Settings scene for modifying user settings."""

import pygame
import pygame_gui
from typing import Dict, Optional

from events import CHANGE_MUSIC, CHANGE_MUSIC_VOLUME, ChangeMusicEvent, ChangeMusicVolumeEvent, emit_event
from scenes.events import PreviousSceneEvent
from scenes.scene import Scene
from settings import settings, save_settings
from ui_components.return_button import ReturnButton
from game_constants import gc

class SettingsScene(Scene):
    """Scene for modifying user settings."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager):
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.sliders: Dict[str, pygame_gui.elements.UIHorizontalSlider] = {}
        self.initial_values: Dict[str, float] = {}  # Store initial values
        self.confirmation_dialog: Optional[pygame_gui.elements.UIConfirmationDialog] = None
        self.create_ui()

    def has_unsaved_changes(self) -> bool:
        """Check if there are any unsaved changes in the settings."""
        for setting_name, slider in self.sliders.items():
            if slider.get_current_value() != self.initial_values[setting_name]:
                return True
        return False

    def create_ui(self) -> None:
        """Create the UI elements for the settings scene."""
        # Create return button
        self.return_button = ReturnButton(self.manager)

        # Create a panel to hold settings
        panel_width = 400
        panel_height = 270
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
        click_increment = 0.1

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

        self.initial_values["SOUND_VOLUME"] = settings.SOUND_VOLUME
        self.sliders["SOUND_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.SOUND_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel,
            click_increment=click_increment
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

        self.initial_values["MUSIC_VOLUME"] = settings.MUSIC_VOLUME
        self.sliders["MUSIC_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.MUSIC_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel,
            click_increment=click_increment
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
            container=settings_panel,
        )

        self.initial_values["VOICE_VOLUME"] = settings.VOICE_VOLUME
        self.sliders["VOICE_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.VOICE_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel,
            click_increment=click_increment
        )
        
        # Drum Volume
        y_offset += element_height + padding
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (label_width, element_height)
            ),
            text="Banner Bearer Volume",
            manager=self.manager,
            container=settings_panel,
        )

        self.initial_values["DRUM_VOLUME"] = settings.DRUM_VOLUME
        self.sliders["DRUM_VOLUME"] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(
                (label_width + padding, y_offset),
                (slider_width, element_height)
            ),
            start_value=settings.DRUM_VOLUME,
            value_range=(0.0, 1.0),
            manager=self.manager,
            container=settings_panel,
            click_increment=click_increment
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

        if self.has_unsaved_changes():
            self.save_button.enable()
        else:
            self.save_button.disable()

        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if self.handle_confirmation_dialog_keys(event):
                continue

            self.handle_escape(event)

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED or event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    # There is a bug where UI_HORIZONTAL_SLIDER_MOVED is not triggered when the end buttons are pressed,
                    # so this fires more often than it should.
                    if settings.MUSIC_VOLUME != self.sliders["MUSIC_VOLUME"].get_current_value():
                        settings.MUSIC_VOLUME = self.sliders["MUSIC_VOLUME"].get_current_value()
                        emit_event(CHANGE_MUSIC_VOLUME, event=ChangeMusicVolumeEvent(
                            volume=settings.MUSIC_VOLUME,
                        ))
                    settings.SOUND_VOLUME = self.sliders["SOUND_VOLUME"].get_current_value()
                    settings.VOICE_VOLUME = self.sliders["VOICE_VOLUME"].get_current_value()
                    settings.DRUM_VOLUME = self.sliders["DRUM_VOLUME"].get_current_value()
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.save_button:
                        save_settings()
                        self.initial_values = {
                            "MUSIC_VOLUME": settings.MUSIC_VOLUME,
                            "SOUND_VOLUME": settings.SOUND_VOLUME,
                            "VOICE_VOLUME": settings.VOICE_VOLUME,
                            "DRUM_VOLUME": settings.DRUM_VOLUME,
                        }
                    elif event.ui_element == self.return_button:
                        if self.has_unsaved_changes():
                            self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
                                rect=pygame.Rect((pygame.display.Info().current_w/2 - 150, pygame.display.Info().current_h/2 - 100), (300, 200)),
                                manager=self.manager,
                                window_title="Unsaved Changes",
                                action_long_desc="You have unsaved changes. Are you sure you want to leave?",
                                action_short_name="Leave",
                                blocking=True
                            )
                        else:
                            pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())
                elif event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if event.ui_element == self.confirmation_dialog:
                        # Revert to initial values before leaving
                        for setting_name, value in self.initial_values.items():
                            setattr(settings, setting_name, value)
                        emit_event(CHANGE_MUSIC_VOLUME, event=ChangeMusicVolumeEvent(
                            volume=settings.MUSIC_VOLUME,
                        ))
                        pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())

            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)