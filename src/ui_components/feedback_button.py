"""Provides the FeedbackButton class for opening feedback form."""

import webbrowser
import pygame
import pygame_gui
from pygame_gui.elements import UIButton


class FeedbackButton(UIButton):
    """A button that opens the feedback form in a web browser.
    
    A specialized UIButton positioned below the return button.
    """
    
    FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSewkbDOhxdRTg1bijS4U8ijBEGcrVaV--Uzh9mmcgOILmUjBQ/viewform?usp=header"
    
    def __init__(self, manager: pygame_gui.UIManager) -> None:
        """Initialize the feedback button.
        
        Args:
            manager: The UI manager that will handle this button.
        """
        super().__init__(
            relative_rect=pygame.Rect((10, 50), (100, 30)),  # 10px below return button
            text="Feedback",
            manager=manager
        )
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle button click events.
        
        Args:
            event: The pygame event to handle.
            
        Returns:
            True if the event was handled, False otherwise.
        """
        if (event.type == pygame.USEREVENT and 
            event.user_type == pygame_gui.UI_BUTTON_PRESSED and 
            event.ui_element == self):
            webbrowser.open(self.FEEDBACK_URL)
            return True