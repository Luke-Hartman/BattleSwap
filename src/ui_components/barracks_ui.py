"""Provides the BarracksUI component for managing available units."""
from typing import Dict, List, Optional
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel, UIScrollingContainer, UIButton, UILabel

import battles
from components.unit_type import UnitType
from entities.units import unit_theme_ids, unit_values
from selected_unit_manager import selected_unit_manager
from progress_manager import progress_manager

class UnitCount(UIPanel):
    """A custom UI button that displays a unit icon and its count."""
    
    size = 64
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        unit_type: UnitType,
        count: int,
        interactive: bool,
        manager: pygame_gui.UIManager,
        infinite: bool,
        container: Optional[pygame_gui.core.UIContainer] = None,
    ):
        """Initialize the unit list item button."""
        self.unit_type = unit_type
        self.infinite = infinite
        self.manager = manager
        super().__init__(
            relative_rect=pygame.Rect((x_pos, y_pos), (self.size, self.size)),
            manager=manager,
            container=container,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        )
        self.button = UIButton(
            relative_rect=pygame.Rect((0, 0), (self.size, self.size)),
            manager=manager,
            text="",
            container=self,
            object_id=ObjectID(class_id="@unit_count", object_id=unit_theme_ids[unit_type]),
        )
        self.button.can_hover = lambda: True
        self.count_label = UILabel(
            relative_rect=pygame.Rect((0, self.size - 25), (self.size, 25)),
            text="inf" if infinite else str(count),
            manager=manager,
            container=self,
            object_id=ObjectID(class_id="@unit_count_text"),
        )
        if not interactive:
            self.button.disable()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for this unit count."""
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED and event.ui_element == self.button:
            selected_unit_manager.selected_unit_type = self.unit_type
            return True
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED and event.ui_element == self.button:
            selected_unit_manager.selected_unit_type = None
            return True
        return False



class BarracksUI(UIPanel):
    """UI component for managing available units in the barracks."""

    def __init__(
            self,
            manager: pygame_gui.UIManager,
            starting_units: Dict[UnitType, int],
            interactive: bool,
            sandbox_mode: bool,
    ):
        """Initialize the barracks UI panel.
        
        Args:
            manager: The UI manager that will handle this component
            starting_units: Dictionary mapping unit types to their initial counts
            interactive: Whether the buttons are interactive
            sandbox_mode: If True, all units are available with infinite count
        """
        self.manager = manager
        self._units = starting_units.copy()
        self.interactive = interactive
        self.sandbox_mode = sandbox_mode
        self.selected_unit_type: Optional[UnitType] = None
        
        # In sandbox mode, make all unit types available
        if sandbox_mode:
            self._units = {unit_type: float('inf') for unit_type in UnitType}
        else:
            # Add any unit types that have been encountered in solved battles with 0 count
            encountered_units = set(starting_units.keys())
            for hex_coords in progress_manager.solutions:
                battle = battles.get_battle_coords(hex_coords)
                for enemy_type, _ in battle.enemies:
                    encountered_units.add(enemy_type)

            # Add encountered units with 0 count if not already present
            for unit_type in encountered_units:
                if unit_type not in self._units:
                    self._units[unit_type] = 0
        
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding
        padding = 10
        
        needs_scrollbar, panel_height = self._calculate_panel_dimensions()
        
        # Position the panel at the bottom of the screen
        y_position = pygame.display.Info().current_h - panel_height - 10
        
        panel_rect = pygame.Rect(
            (side_padding, y_position),
            (panel_width, panel_height)
        )
        
        super().__init__(
            relative_rect=panel_rect,
            manager=manager
        )
        
        self.unit_list_items: List[UnitCount] = []
        self._create_container(panel_width, panel_height, padding, needs_scrollbar)
        self._populate_units(padding, needs_scrollbar)

    def _calculate_panel_dimensions(self) -> tuple[bool, int]:
        """Calculate if scrollbar is needed and return appropriate panel height."""
        padding = 10
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding
        
        # Count all units, including those with 0 count
        visible_unit_count = len(self._units)
        total_width = visible_unit_count * (UnitCount.size + padding // 2) - padding // 2 if visible_unit_count > 0 else 0
        needs_scrollbar = total_width > panel_width - 2 * padding
        panel_height = 110 if needs_scrollbar else 85
        
        return needs_scrollbar, panel_height

    def _create_container(self, panel_width: int, panel_height: int, padding: int, needs_scrollbar: bool) -> None:
        """Create the scrolling container for unit items."""
        container_height = panel_height - 2 * padding
        container_rect = pygame.Rect(
            (padding, padding),
            (panel_width - 2 * padding, container_height)
        )
        
        self.unit_container = UIScrollingContainer(
            relative_rect=container_rect,
            manager=self.manager,
            container=self,
            allow_scroll_y=False,
        )

    def _populate_units(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate the container with unit items."""
        container_height = self.unit_container.rect.height
        y_offset = (container_height - UnitCount.size) // 2 if not needs_scrollbar else 0
        
        x_position = 0
        # Alphabetically sort the units
        unit_order = sorted(
            self._units.items(),
            key=lambda x: x[0].value
        )
        for unit_type, count in unit_order:
            item = UnitCount(
                x_pos=x_position,
                y_pos=y_offset,
                unit_type=unit_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=self.unit_container,
                infinite=self.sandbox_mode
            )
            self.unit_list_items.append(item)
            x_position += item.size + padding // 2

    def _rebuild(self) -> None:
        """Rebuild the entire UI when structure needs to change."""
        self.unit_container.kill()
        for item in self.unit_list_items:
            item.kill()
        
        needs_scrollbar, _ = self._calculate_panel_dimensions()
        self._create_container(
            self.rect.width,
            self.rect.height,
            10,  # padding
            needs_scrollbar
        )
        self._populate_units(10, needs_scrollbar)

    def add_unit(self, unit_type: UnitType) -> None:
        """Add one unit of the specified type to the barracks.
        
        Args:
            unit_type: The type of unit to add
        """
        self._units[unit_type] += 1
        self._rebuild()

    def remove_unit(self, unit_type: UnitType) -> None:
        """Remove one unit of the specified type from the barracks.
        
        Args:
            unit_type: The type of unit to remove
        """
        assert self._units[unit_type] > 0
        self._units[unit_type] -= 1
        self._rebuild()

    def select_unit_type(self, unit_type: Optional[UnitType]) -> None:
        """Select the specified unit type."""
        for item in self.unit_list_items:
            if item.unit_type == unit_type:
                item.button.select()
            elif item.button.is_selected:
                item.button.unselect()

    @property
    def units(self) -> Dict[UnitType, int]:
        """Get the current unit counts.
        
        Returns:
            Dictionary mapping unit types to their current counts
        """
        return self._units.copy()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for the barracks.
        
        Args:
            event: The pygame event to handle
            
        Returns:
            True if the event was handled, False otherwise
        """
        # Pass event to all unit count items
        for item in self.unit_list_items:
            if item.handle_event(event):
                return True
                
        return False