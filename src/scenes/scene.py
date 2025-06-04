from abc import ABC

import pygame
import pygame_gui

from events import PLAY_SOUND, PlaySoundEvent, emit_event

class Scene(ABC):
    """Abstract base class for all scenes."""

    def __init__(self) -> None:
        """Initialize the scene."""
        pass

    def handle_escape(self, event: pygame.event.Event) -> None:
        """Handle escape key press by triggering the return button if it exists."""
        if (event.type == pygame.KEYDOWN and 
            event.key == pygame.K_ESCAPE and 
            hasattr(self, 'return_button')):
            # Create and post a button press event for the return button
            button_event = pygame.event.Event(
                pygame.USEREVENT,
                {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': self.return_button}
            )
            pygame.event.post(button_event)

    def handle_confirmation_dialog_keys(self, event: pygame.event.Event) -> bool:
        """Handle keyboard events for confirmation dialogs.
        
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if (event.type == pygame.KEYDOWN and 
            hasattr(self, 'confirmation_dialog') and 
            self.confirmation_dialog is not None):

            if event.key == pygame.K_RETURN:
                # Simulate clicking the confirm button
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, {
                    'user_type': pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED,
                    'ui_element': self.confirmation_dialog,
                }))
                return True
            elif event.key == pygame.K_ESCAPE:
                # Simulate clicking the cancel button
                self.confirmation_dialog.kill()
                self.confirmation_dialog = None
                return True
        return False

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
            if event.type == pygame_gui.UI_BUTTON_ON_HOVERED:
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_hover.wav",
                    volume=0.5
                ))
        return True
