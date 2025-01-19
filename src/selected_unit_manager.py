"""Service for managing the stats card UI."""
from typing import Optional
import pygame
import pygame_gui

from components.unit_type import UnitType
from stats_cards import get_stats_card_text

class SelectedUnitManager:
    """Service for managing the stats card UI."""

    def __init__(self):
        """Initialize the stats card manager."""
        self.stats_card_ui: Optional[pygame_gui.elements.UITextBox] = None
        self._selected_unit_type: Optional[UnitType] = None
        self.manager: Optional[pygame_gui.UIManager] = None

    def initialize(self, manager: pygame_gui.UIManager) -> None:
        """Initialize with the UI manager."""
        self.manager = manager

    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        return self._selected_unit_type
    
    @selected_unit_type.setter
    def selected_unit_type(self, value: Optional[UnitType]) -> None:
        self._selected_unit_type = value
        if value is not None:
            self._show_stats()
        else:
            self._hide_stats()

    def _show_stats(self) -> None:
        """Show the stats card for a unit type."""
        if self.manager is None:
            return
        self._hide_stats()  # Clean up any existing stats card
        assert self._selected_unit_type is not None
        text = "\n".join(get_stats_card_text(self._selected_unit_type))
        self.stats_card_ui = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(0, 0, 300, -1),
            html_text=text,
            wrap_to_height=True,
            manager=self.manager
        )
        # Position in middle right of screen
        self.stats_card_ui.rect.midright = (
            pygame.display.get_surface().get_width() - 10,
            pygame.display.get_surface().get_height()/2
        )

    def _hide_stats(self) -> None:
        """Hide the stats card if it exists."""
        if self.stats_card_ui is not None:
            self.stats_card_ui.kill()
            self.stats_card_ui = None

selected_unit_manager = SelectedUnitManager()