"""Service for managing the stats card UI."""
from typing import Optional
import pygame
import pygame_gui

from components.unit_type import UnitType
from ui_components.unit_card import UnitCard
from ui_components.game_data import UNIT_DATA
from ui_components.game_data import StatType

class SelectedUnitManager:
    """Service for managing the stats card UI."""

    def __init__(self):
        """Initialize the stats card manager."""
        self.unit_card: Optional[UnitCard] = None
        self._selected_unit_type: Optional[UnitType] = None
        self.manager: Optional[pygame_gui.UIManager] = None
        self.screen: Optional[pygame.Surface] = None

    def initialize(self, manager: pygame_gui.UIManager) -> None:
        """Initialize with the UI manager."""
        self.manager = manager
        self.screen = pygame.display.get_surface()

    def update(self, time_delta: float) -> None:
        """Update the unit card animations."""
        if self.unit_card is not None:
            self.unit_card.update(time_delta)

    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        return self._selected_unit_type
    
    @selected_unit_type.setter
    def selected_unit_type(self, value: Optional[UnitType]) -> None:
        if self._selected_unit_type != value:
            self._hide_stats()
            self._selected_unit_type = value
            self._show_stats()

    def _show_stats(self) -> None:
        """Show the unit card for a unit type."""
        if self.manager is None or self.screen is None:
            return
        if self._selected_unit_type is None:
            return
        
        # Get unit data
        unit_data = UNIT_DATA[self._selected_unit_type]
        
        # Calculate position in middle right of screen (same as before)
        card_width = 300
        card_height = 475
        position = (
            self.screen.get_width() - card_width - 10,
            (self.screen.get_height() - card_height) // 2
        )
        
        # Create the unit card
        self.unit_card = UnitCard(
            screen=self.screen,
            manager=self.manager,
            position=position,
            name=unit_data["name"],
            description=unit_data["description"],
            unit_type=self._selected_unit_type
        )
        
        # Add all stats to the card, with non-applicable ones being grayed out
        for stat_type in StatType:
            if stat_type in unit_data["stats"]:
                self.unit_card.add_stat(
                    stat_type=stat_type,
                    value=unit_data["stats"][stat_type],
                    tooltip_text=unit_data["tooltips"][stat_type]
                )
            else:
                self.unit_card.skip_stat(
                    stat_type=stat_type
                )

    def _hide_stats(self) -> None:
        """Hide the unit card if it exists."""
        if self.unit_card is not None:
            self.unit_card.kill()
            self.unit_card = None

selected_unit_manager = SelectedUnitManager()