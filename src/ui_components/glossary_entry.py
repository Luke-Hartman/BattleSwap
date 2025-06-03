import pygame
import pygame_gui
from typing import Optional, Tuple

class GlossaryEntry:
    """A UI component that displays a glossary entry with a title and content."""
    
    def __init__(self, 
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 title: str,
                 content: str):
        """
        Initialize a GlossaryEntry component.
        
        Args:
            manager: The UI manager for this component
            position: The (x, y) position to place the window
            title: The title of the glossary entry
            content: The HTML content of the glossary entry (can include links)
        """
        self.manager = manager
        self.title = title
        self.content = content
        self.creation_index = None  # Used for positioning in the card system
        
        # Use same dimensions as unit cards
        width = 300
        height = 475
        
        # Create the window
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(position, (width, height)),
            window_display_title=title,
            manager=manager,
            resizable=False
        )
        
        # Add text to the window with clickable words
        # Leave more space for content since we don't have other elements like unit cards
        self.text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((0, 0), (300, 445)),
            html_text=content,
            manager=manager,
            container=self.window
        )
        
        # Store the window reference in the text box's container for link handling
        self.text.ui_container.window = self.window
    
    def get_window(self):
        """Get the window element for this glossary entry."""
        return self.window
    
    def kill(self):
        """Remove the glossary entry from the UI."""
        self.window.kill()
        
    def bring_to_front(self):
        """Bring this glossary entry to the front."""
        if self.window.alive():
            # Use pygame-gui's built-in bring_to_front method if available
            if hasattr(self.manager, 'bring_to_front'):
                self.manager.bring_to_front(self.window)
            # Fallback: use the window's change_layer method
            elif hasattr(self.window, 'change_layer'):
                # Find the highest layer currently in use and add 1
                current_max = 0
                for element in self.manager.get_root_container().elements:
                    if hasattr(element, '_layer'):
                        current_max = max(current_max, element._layer)
                self.window.change_layer(current_max + 1)
    
    @staticmethod
    def from_click_position(manager: pygame_gui.UIManager, 
                           title: str,
                           content: str,
                           click_position: Optional[Tuple[int, int]] = None,
                           default_position: Tuple[int, int] = (50, 250)):
        """
        Create a glossary entry based on click position with fallbacks.
        
        Args:
            manager: The UI manager
            title: Entry title
            content: Entry content (HTML)
            click_position: Mouse position where clicked (if available)
            default_position: Default position to use if no other positioning is available
            
        Returns:
            A new GlossaryEntry component
        """
        # Calculate position based on click position or default
        if click_position:
            position = click_position
        else:
            position = default_position
            
        return GlossaryEntry(manager, position, title, content) 