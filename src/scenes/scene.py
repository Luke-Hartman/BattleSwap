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
        """Handle escape key press by closing windows first, then triggering return button."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.5
            ))
            # First, try to close any scene-specific windows
            if self._close_scene_windows():
                return
            
            # If no windows were closed, fall back to default behavior (return button)
            if hasattr(self, 'return_button'):
                # Create and post a button press event for the return button
                button_event = pygame.event.Event(
                    pygame.USEREVENT,
                    {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': self.return_button}
                )
                pygame.event.post(button_event)

    def _close_scene_windows(self) -> bool:
        """Close any open windows specific to this scene. 
        
        Override this method in subclasses to handle scene-specific windows.
        Returns True if any windows were closed, False otherwise.
        """
        # Import here to avoid circular imports
        from selected_unit_manager import selected_unit_manager
        
        windows_closed = False
        
        # Handle unit cards that are common across scenes
        if selected_unit_manager.unit_cards:
            # Close all unit cards at once
            for card in selected_unit_manager.unit_cards:
                card.kill()
            selected_unit_manager.unit_cards.clear()
            windows_closed = True
            
        # Handle glossary entries that are common across scenes
        if selected_unit_manager.glossary_entries:
            # Close all glossary entries at once
            for entry in selected_unit_manager.glossary_entries:
                entry.kill()
            selected_unit_manager.glossary_entries.clear()
            windows_closed = True
            
        # Handle single unit card in normal mode
        if selected_unit_manager.unit_card is not None:
            selected_unit_manager.unit_card.kill()
            selected_unit_manager.unit_card = None
            windows_closed = True
        
        return windows_closed

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
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
            elif event.key == pygame.K_ESCAPE:
                # Simulate clicking the cancel button
                self.confirmation_dialog.kill()
                self.confirmation_dialog = None
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
        return False

    def handle_confirmation_dialog_events(self, event: pygame.event.Event) -> bool:
        """Handle confirmation dialog cancel button clicks.
        
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if (event.type == pygame.USEREVENT and 
            event.user_type == pygame_gui.UI_BUTTON_PRESSED and
            hasattr(self, 'confirmation_dialog') and 
            self.confirmation_dialog is not None):
            
            # Check if the clicked button is the cancel button of our confirmation dialog
            if (hasattr(self.confirmation_dialog, 'cancel_button') and 
                event.ui_element == self.confirmation_dialog.cancel_button):
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
