"""Provides the BattleButton class for the battle setup screen."""

import pygame
import pygame_gui
from pygame_gui.elements import UIButton
from keyboard_shortcuts import format_button_text, KeyboardShortcuts
from screen_dimensions import get_width, get_height


class StartButton(UIButton):
    """A button that triggers battle start.
    
    A specialized UIButton positioned at the bottom center of the screen.
    """
    
    def __init__(self, manager: pygame_gui.UIManager) -> None:
        """Initialize the battle button.
        
        Args:
            manager: The UI manager that will handle this button.
        """
        button_width = 100
        button_height = 30
        
        button_rect = pygame.Rect(
            (get_width() - button_width - 10, 10),
            (button_width, button_height)
        )
        
        super().__init__(
            relative_rect=button_rect,
            text=format_button_text("Start", KeyboardShortcuts.ENTER),
            manager=manager
        )