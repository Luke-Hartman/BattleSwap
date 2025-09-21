"""UI component for item count buttons."""

import pygame
import pygame_gui
from typing import Optional
from ui_components.base_count_button import BaseCountButton
from entities.items import ItemType, item_registry
from point_values import item_values
from ui_components.game_data import get_item_data
from selected_unit_manager import selected_unit_manager


class ItemCount(BaseCountButton):
    """A UI button that displays an item icon and its count."""
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        item_type: ItemType,
        count: int,
        interactive: bool,
        manager: pygame_gui.UIManager,
        infinite: bool = False,
        container: Optional[pygame_gui.core.UIContainer] = None,
    ):
        self.item_type = item_type
        super().__init__(
            x_pos=x_pos,
            y_pos=y_pos,
            count=count,
            interactive=interactive,
            manager=manager,
            infinite=infinite,
            container=container
        )
        
        # Set up tooltip for items
        item_data = get_item_data(item_type)
        points = item_values[item_type]
        self.tool_tip_text = f"{item_data.name}\n{item_data.description}\nPoints: {points}"
        self.tool_tip_delay = 0
    
    def _get_button_object_id(self) -> pygame_gui.core.ObjectID:
        """Get the appropriate object ID for the item button."""
        if self.item_type == ItemType.HEALTH_POTION:
            return pygame_gui.core.ObjectID(
                class_id="@item_count",
                object_id="#health_potion_icon"
            )
        else:
            # Fallback to generic item theme for other items
            return pygame_gui.core.ObjectID(
                class_id="@item_count",
                object_id=f"#item_count_{self.item_type.value}"
            )
    
    def _get_point_value(self) -> int:
        """Get the point value for this item."""
        return item_values[self.item_type]
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for the item button."""
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED and event.ui_element == self.button:
            selected_unit_manager.set_selected_item(self.item_type)
            return True
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED and event.ui_element == self.button:
            selected_unit_manager.set_selected_item(None)
            return True
        return False
