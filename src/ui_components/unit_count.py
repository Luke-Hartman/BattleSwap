"""UI component for unit count buttons."""

import pygame
import pygame_gui
from typing import Optional
from ui_components.base_count_button import BaseCountButton
from components.unit_type import UnitType
from entities.units import get_unit_icon_theme_class, unit_theme_ids
from point_values import unit_values
from selected_unit_manager import selected_unit_manager
from progress_manager import progress_manager


class UnitCount(BaseCountButton):
    """A UI button that displays a unit icon and its count."""
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        unit_type: UnitType,
        count: int,
        interactive: bool,
        manager: pygame_gui.UIManager,
        infinite: bool = False,
        container: Optional[pygame_gui.core.UIContainer] = None,
        hotkey: Optional[str] = None,
    ):
        self.unit_type = unit_type
        super().__init__(
            x_pos=x_pos,
            y_pos=y_pos,
            count=count,
            interactive=interactive,
            manager=manager,
            infinite=infinite,
            container=container,
            hotkey=hotkey
        )
    
    def _get_button_object_id(self) -> pygame_gui.core.ObjectID:
        """Get the appropriate object ID for the unit button."""
        unit_tier = progress_manager.get_unit_tier(self.unit_type)
        tier_theme_class = get_unit_icon_theme_class(unit_tier)
        return pygame_gui.core.ObjectID(
            class_id=tier_theme_class, 
            object_id=unit_theme_ids[self.unit_type]
        )
    
    def _get_point_value(self) -> int:
        """Get the point value for this unit."""
        return unit_values[self.unit_type]
    
    def refresh_tier_styling(self) -> None:
        """Update the tier-specific styling for this unit icon."""
        unit_tier = progress_manager.get_unit_tier(self.unit_type)
        tier_theme_class = get_unit_icon_theme_class(unit_tier)
        if tier_theme_class in self.button.class_ids:
            return
        # Update the button's object ID with the new tier theme class
        new_object_id = pygame_gui.core.ObjectID(
            class_id=tier_theme_class, 
            object_id=unit_theme_ids[self.unit_type]
        )
        self.button.change_object_id(new_object_id)
    
    def set_flash_state(self, flash: bool) -> None:
        """Set the flash border state for this unit button."""
        if flash:
            # Use flash theme (white border)
            new_object_id = pygame_gui.core.ObjectID(
                class_id="@unit_count_flash",
                object_id=unit_theme_ids[self.unit_type]
            )
        else:
            # Use no border theme (for flash OFF state)
            new_object_id = pygame_gui.core.ObjectID(
                class_id="@unit_count_no_border",
                object_id=unit_theme_ids[self.unit_type]
            )
        self.button.change_object_id(new_object_id)
    
    def restore_normal_theme(self) -> None:
        """Restore the normal tier-based theme for this unit button."""
        unit_tier = progress_manager.get_unit_tier(self.unit_type)
        tier_theme_class = get_unit_icon_theme_class(unit_tier)
        new_object_id = pygame_gui.core.ObjectID(
            class_id=tier_theme_class,
            object_id=unit_theme_ids[self.unit_type]
        )
        self.button.change_object_id(new_object_id)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for the unit button."""
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED and event.ui_element == self.button:
            selected_unit_manager.set_selected_unit(self.unit_type, None, None)
            return True
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED and event.ui_element == self.button:
            selected_unit_manager.set_selected_unit(None, None, None)
            return True
        return False
