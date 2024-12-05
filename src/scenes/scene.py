from abc import ABC

import pygame
import pygame_gui

from events import PLAY_SOUND, PlaySoundEvent, emit_event

class Scene(ABC):
    """Abstract base class for all scenes."""

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the scene, including rendering and processing events.
        Args:
            time_delta: The time delta since the last update.
            events: The events from pygame.event.get().

        Returns:
            True if the game should continue, False if it should quit.
        """
        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
        return True
