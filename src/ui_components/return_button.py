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
        self._clicked = False  # Track if button has been clicked
    
    def process_event(self, event: pygame.event.Event) -> bool:
        """Override process_event to prevent multiple rapid clicks.
        
        Args:
            event: The pygame event to process.
            
        Returns:
            bool: True if the event was consumed, False otherwise.
        """
        # If we've already been clicked, consume all events to prevent further processing
        if self._clicked:
            return True
            
        # Process the event normally
        consumed = super().process_event(event)
        
        # If this was a button press event, disable ourselves to prevent rapid clicking
        if (consumed and 
            event.type == pygame.USEREVENT and 
            hasattr(event, 'user_type') and 
            event.user_type == pygame_gui.UI_BUTTON_PRESSED and
            hasattr(event, 'ui_element') and 
            event.ui_element == self):
            self._clicked = True
            self.disable()
        
        return consumed 