"""Provides the BarracksUI component for managing available units."""
from typing import Dict, List, Optional
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel, UIScrollingContainer, UIButton

from components.unit_type import UnitType
from entities.units import unit_theme_ids, unit_icon_surfaces


class UnitCount(UIButton):
    """A custom UI button that displays a unit icon and its count."""
    
    size = 64
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        unit_type: UnitType,
        count: int,
        interactive: bool,
        manager: pygame_gui.UIManager,
        container: Optional[pygame_gui.core.UIContainer] = None,
    ):
        """Initialize the unit list item button."""
        super().__init__(
            relative_rect=pygame.Rect((x_pos, y_pos), (self.size, self.size)),
            text=str(count),
            manager=manager,
            container=container,
            object_id=ObjectID(class_id="@unit_count", object_id=unit_theme_ids[unit_type])
        )
        if not interactive:
            self.disable()
        self.unit_type = unit_type


class BarracksUI(UIPanel):
    """UI component for managing available units in the barracks."""

    def __init__(
            self,
            manager: pygame_gui.UIManager,
            starting_units: Dict[UnitType, int],
            interactive: bool,
    ):
        """Initialize the barracks UI panel.
        
        Args:
            manager: The UI manager that will handle this component
            starting_units: Dictionary mapping unit types to their initial counts
            interactive: Whether the buttons are interactive
        """
        self.manager = manager
        self._units = starting_units.copy()
        self.interactive = interactive
        
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding
        padding = 10
        
        needs_scrollbar, panel_height = self._calculate_panel_dimensions()
        
        panel_rect = pygame.Rect(
            (side_padding, pygame.display.Info().current_h - panel_height - 10),
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
        
        visible_unit_count = sum(1 for _, count in self._units.items() if count > 0)
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
        for unit_type, count in self._units.items():
            if count > 0:
                item = UnitCount(
                    x_pos=x_position,
                    y_pos=y_offset,
                    unit_type=unit_type,
                    count=count,
                    interactive=self.interactive,
                    manager=self.manager,
                    container=self.unit_container
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

    @property
    def units(self) -> Dict[UnitType, int]:
        """Get the current unit counts.
        
        Returns:
            Dictionary mapping unit types to their current counts
        """
        return self._units.copy()