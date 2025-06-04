"""Provides the ReturnButton class for scene navigation."""

import pygame
import pygame_gui
from pygame_gui.elements import UIButton


class ReturnButton(UIButton):
    """A button that returns to the previous scene.
    
    A specialized UIButton positioned at the top left corner of the screen.
    """
    
    def __init__(self, manager: pygame_gui.UIManager) -> None:
        """Initialize the return button.
        
        Args:
            manager: The UI manager that will handle this button.
        """
        super().__init__(
            relative_rect=pygame.Rect((10, 10), (100, 30)),
            text="Return",
            manager=manager
        ) 
        self._clicked_and_disabled = False
    
    def process_event(self, event: pygame.event.Event) -> bool:
        """Override process_event to prevent multiple rapid clicks.
        
        Args:
            event: The pygame event to process.
            
        Returns:
            bool: True if the event was consumed, False otherwise.
        """
        # This is to prevent the button from being clicked multiple times in a row
        if event.type == pygame.MOUSEBUTTONUP:
            if self._clicked_and_disabled:
                return False
            self._clicked_and_disabled = True
            return super().process_event(event)
        return super().process_event(event)
