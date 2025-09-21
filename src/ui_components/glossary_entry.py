import pygame
import pygame_gui
import pygame_gui.core
from typing import Optional, Tuple
from ui_components.base_card import BaseCard

class GlossaryEntry(BaseCard):
    """A UI component that displays a glossary entry with a title and content."""
    
    def __init__(self, 
                 screen: pygame.Surface,
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 title: str,
                 content: str):
        """
        Initialize a GlossaryEntry component.
        
        Args:
            screen: The pygame surface
            manager: The UI manager for this component
            position: The (x, y) position to place the window
            title: The title of the glossary entry
            content: The HTML content of the glossary entry (can include links)
        """
        self.content = content
        
        # Initialize base card
        super().__init__(
            screen=screen,
            manager=manager,
            position=position,
            title=title,
            container=None,
            padding=0
        )
    
    def _create_card_content(self) -> None:
        """Create the glossary entry content."""
        # Add text to the window with clickable words
        # Leave more space for content since we don't have other elements like unit cards
        self.text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((0, 0), (self.width, self.height - 40)),
            html_text=self.content,
            manager=self.manager,
            container=self.card_container
        )
        
        # Store the window reference in the text box's container for link handling
        self.text.ui_container.window = self.window
    
    def _kill_card_elements(self) -> None:
        """Kill glossary entry specific elements."""
        self.text.kill()
    
    