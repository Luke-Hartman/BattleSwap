import pygame
import pygame_gui
import pygame_gui.core
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
        
        # Flash animation state
        self.flash_time = 0.0
        self.flash_duration = 1.0  # Total flash duration in seconds
        self.flash_alternations = 6  # Number of border switches (3 full cycles)
        self.flash_interval = self.flash_duration / self.flash_alternations
        self.is_flashing = False
        self.flash_state = False  # False = normal, True = flash theme
        
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
            relative_rect=pygame.Rect((0, 0), (300, 435)),
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
        """Bring this glossary entry to the front with a flash effect."""
        if self.window.alive():
            # Use pygame-gui's window stack to bring window to front
            window_stack = self.manager.get_window_stack()
            window_stack.move_window_to_front(self.window)
        
        # Start flash animation
        self.start_flash()
    
    def start_flash(self):
        """Start the flash animation effect."""
        if self.window.alive():
            self.is_flashing = True
            self.flash_time = 0.0
            self.flash_state = False
    
    def _update_flash_theme(self):
        """Update the window theme based on flash state."""
        if self.window.alive():
            if self.flash_state:
                # Switch to flash theme
                self.window.change_object_id(pygame_gui.core.ObjectID(object_id='#flash_window'))
            else:
                # Switch back to normal theme
                self.window.change_object_id(pygame_gui.core.ObjectID(class_id='window'))
    
    def update(self, time_delta: float):
        """Update the flash animation."""
        if self.is_flashing:
            self.flash_time += time_delta
            
            # Calculate current alternation
            current_alternation = int(self.flash_time / self.flash_interval)
            new_flash_state = (current_alternation % 2) == 1
            
            # Update theme if state changed
            if new_flash_state != self.flash_state:
                self.flash_state = new_flash_state
                self._update_flash_theme()
            
            # End flash after all alternations
            if self.flash_time >= self.flash_duration:
                self.is_flashing = False
                self.flash_time = 0.0
                self.flash_state = False
                self._update_flash_theme()  # Ensure we end on normal theme
    
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