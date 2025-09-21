"""UI component for item cards."""

import pygame
import pygame_gui
import pygame_gui.core
from typing import Tuple, Optional
from entities.items import ItemType
from ui_components.game_data import get_item_data
from ui_components.base_card import BaseCard

class ItemCard(BaseCard):
    """A simple UI component that displays an item card with just the description."""
    
    def __init__(self, 
                 screen: pygame.Surface,
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 item_type: ItemType,
                 container: Optional[pygame_gui.core.UIContainer] = None,
                 padding: int = 0):
        """
        Initialize an ItemCard component.
        
        Args:
            screen: The pygame surface
            manager: The UI manager for this component
            position: The (x, y) position to place the window (ignored if container is provided)
            item_type: The type of item to display
            container: Optional container to place the card in (if None, creates a window)
            padding: Padding around the item card
        """
        self.item_type = item_type
        
        # Get item data
        self.item_data = get_item_data(item_type)
        
        # Initialize base card
        super().__init__(
            screen=screen,
            manager=manager,
            position=position,
            title=self.item_data.name,
            container=container,
            padding=padding
        )
    
    def _create_card_content(self) -> None:
        """Create the item card content."""
        # Add description
        self.description_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.padding, self.padding),
                (self.width - 2 * self.padding, self.height - 2 * self.padding)
            ),
            text=self.item_data.description,
            manager=self.manager,
            container=self.card_container
        )
    
    def _kill_card_elements(self) -> None:
        """Kill item card specific elements."""
        self.description_label.kill()
