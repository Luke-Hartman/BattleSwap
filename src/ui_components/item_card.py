"""UI component for item cards."""

import pygame
import pygame_gui
import pygame_gui.core
from typing import Tuple, Optional
from entities.items import ItemType, item_icon_surfaces
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
        """Create the item card content with icon at top and description below."""
        # Calculate dimensions
        card_width = self.width - 2 * self.padding
        icon_size = card_width  # Icon takes full width of card
        text_height = self.height - icon_size - 2 * self.padding - 40  # Leave space for icon and padding
        
        # Add item icon at the top, scaled to full card width
        icon_surface = item_icon_surfaces[self.item_type]
        icon_width, icon_height = icon_surface.get_size()
        
        # Scale icon to fit the card width while maintaining aspect ratio
        scale_factor = icon_size / max(icon_width, icon_height)
        scaled_width = int(icon_width * scale_factor)
        scaled_height = int(icon_height * scale_factor)
        
        # Center the icon horizontally
        icon_x = self.padding + (card_width - scaled_width) // 2
        icon_y = self.padding
        
        # Create UIImage for the icon
        self.item_icon = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(
                (icon_x, icon_y),
                (scaled_width, scaled_height)
            ),
            image_surface=pygame.transform.scale(icon_surface, (scaled_width, scaled_height)),
            manager=self.manager,
            container=self.card_container
        )
        
        # Add description text box below the icon
        text_y = icon_y + scaled_height + 10  # 10px gap between icon and text
        self.description_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(
                (self.padding, text_y),
                (card_width, text_height)
            ),
            html_text=self.item_data.description,
            manager=self.manager,
            container=self.card_container
        )
        
        # Store the window reference in the text box's container for link handling
        if self.window is not None:
            self.description_text.ui_container.window = self.window
        elif hasattr(self.container, 'window'):
            self.description_text.ui_container.window = self.container.window
    
    def _kill_card_elements(self) -> None:
        """Kill item card specific elements."""
        if self.item_icon is not None:
            self.item_icon.kill()
        self.description_text.kill()
