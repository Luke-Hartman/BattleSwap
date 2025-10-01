"""UI component for spell count buttons."""

import pygame
import pygame_gui
from typing import Optional
from ui_components.base_count_button import BaseCountButton
from components.spell_type import SpellType
from entities.spells import spell_theme_ids
from point_values import spell_values
from selected_unit_manager import selected_unit_manager


class SpellCount(BaseCountButton):
    """A UI button that displays a spell icon and its count."""
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        spell_type: SpellType,
        count: int,
        interactive: bool,
        manager: pygame_gui.UIManager,
        infinite: bool = False,
        container: Optional[pygame_gui.core.UIContainer] = None,
        hotkey: Optional[str] = None,
    ):
        self.spell_type = spell_type
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
        """Get the appropriate object ID for the spell button."""
        return pygame_gui.core.ObjectID(
            class_id="@spell_count",
            object_id=spell_theme_ids[self.spell_type]
        )
    
    def _get_point_value(self) -> int:
        """Get the point value for this spell."""
        return spell_values[self.spell_type]
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for the spell button."""
        if not self.interactive:
            return False
            
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.button:
            # Select this spell type
            selected_unit_manager.set_selected_spell_type(self.spell_type)
            return True
        elif event.type == pygame_gui.UI_BUTTON_ON_HOVERED and event.ui_element == self.button:
            # Show hover preview
            selected_unit_manager.set_selected_spell_type(self.spell_type)
            return True
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED and event.ui_element == self.button:
            # Clear hover preview if not actually selected
            if selected_unit_manager._selected_spell_type == self.spell_type:
                selected_unit_manager.set_selected_spell_type(None)
            return True
        return False
