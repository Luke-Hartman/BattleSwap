"""Base class for all card types in the game."""

import pygame
import pygame_gui
import pygame_gui.core
from typing import Tuple, Optional
from abc import ABC, abstractmethod


class BaseCard(ABC):
    """Abstract base class for all card types (UnitCard, ItemCard, GlossaryEntry)."""
    
    # Standard card dimensions
    WIDTH = 300
    HEIGHT = 475
    
    def __init__(self, 
                 screen: pygame.Surface,
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 title: str,
                 container: Optional[pygame_gui.core.UIContainer] = None,
                 padding: int = 0):
        """
        Initialize a BaseCard component.
        
        Args:
            screen: The pygame surface
            manager: The UI manager for this component
            position: The (x, y) position to place the window (ignored if container is provided)
            title: The title to display in the window
            container: Optional container to place the card in (if None, creates a window)
            padding: Padding around the card
        """
        self.screen = screen
        self.manager = manager
        self.title = title
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.container = container
        self.padding = padding
        
        # Add creation_index for positioning system
        self.creation_index: int = 0
        
        # Flash animation state
        self.flash_time = 0.0
        self.flash_duration = 1.0  # Total flash duration in seconds
        self.flash_alternations = 6  # Number of border switches (3 full cycles)
        self.flash_interval = self.flash_duration / self.flash_alternations
        self.is_flashing = False
        self.flash_state = False  # False = normal, True = flash theme
        
        # Create window or use container
        if container is None:
            # Create a window if no container provided
            self.window = pygame_gui.elements.UIWindow(
                rect=pygame.Rect(position, (self.WIDTH, self.HEIGHT)),
                window_display_title=title,
                manager=manager,
                resizable=False
            )
            self.card_container = self.window
        else:
            # Use the provided container
            self.window = None
            self.card_container = container
        
        # Initialize card-specific content
        self._create_card_content()
    
    @abstractmethod
    def _create_card_content(self) -> None:
        """Create the card-specific content. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _kill_card_elements(self) -> None:
        """Kill card-specific UI elements. Must be implemented by subclasses.
        
        If the card has no individual elements to clean up, this method can be empty.
        """
        pass
    
    def get_window(self):
        """Get the window element for this card, or the container if no window."""
        return self.window if self.window is not None else self.card_container
    
    def bring_to_front(self) -> None:
        """Bring this card to the front with a flash effect."""
        if self.window is not None and self.window.alive():
            # Use pygame-gui's window stack to bring window to front
            window_stack = self.manager.get_window_stack()
            window_stack.move_window_to_front(self.window)
        
        # Start flash animation
        self.start_flash()
    
    def start_flash(self) -> None:
        """Start the flash animation effect."""
        if self.window is not None and self.window.alive():
            self.is_flashing = True
            self.flash_time = 0.0
            self.flash_state = False
    
    def _update_flash_theme(self) -> None:
        """Update the window theme based on flash state."""
        if self.window is not None and self.window.alive():
            if self.flash_state:
                # Switch to flash theme
                self.window.change_object_id(pygame_gui.core.ObjectID(object_id='#flash_window'))
            else:
                # Switch back to normal theme
                self.window.change_object_id(pygame_gui.core.ObjectID(class_id='window'))
    
    def update(self, time_delta: float) -> None:
        """Update the flash animation."""
        # Update flash animation
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
    
    def kill(self) -> None:
        """Remove the card from the UI."""
        if self.window:
            self.window.kill()
        else:
            # If using a container, we need to kill individual elements
            self._kill_card_elements()
