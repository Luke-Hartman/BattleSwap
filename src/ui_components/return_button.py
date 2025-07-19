"""Provides the ReturnButton class for scene navigation."""

import pygame
import pygame_gui
from pygame_gui.elements import UIButton
from keyboard_shortcuts import format_button_text, KeyboardShortcuts


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
            text=format_button_text("Return", KeyboardShortcuts.ESCAPE),
            manager=manager
        ) 
        self._clicked_and_disabled = False
