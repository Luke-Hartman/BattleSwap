"""Service for managing the stats card UI."""
from typing import Optional, List, Union
import pygame
import pygame_gui

from components.unit_type import UnitType
from ui_components.unit_card import UnitCard
from ui_components.glossary_entry import GlossaryEntry
from ui_components.game_data import UNIT_DATA
from ui_components.game_data import StatType
from info_mode_manager import info_mode_manager

class SelectedUnitManager:
    """Service for managing the stats card UI."""

    CARD_WIDTH = 300
    CARD_HEIGHT = 475
    CARD_SPACING = 10
    MARGIN = 20
    ROW_OFFSET = 20  # Offset for layered effect

    def __init__(self):
        """Initialize the stats card manager."""
        self.unit_card: Optional[UnitCard] = None  # For normal mode
        self.unit_cards: List[UnitCard] = []  # For info mode (multiple cards)
        self.glossary_entries: List[GlossaryEntry] = []  # For info mode glossary entries
        self._selected_unit_type: Optional[UnitType] = None
        self.manager: Optional[pygame_gui.UIManager] = None
        self.screen: Optional[pygame.Surface] = None

    def initialize(self, manager: pygame_gui.UIManager) -> None:
        """Initialize with the UI manager."""
        self.manager = manager
        self.screen = pygame.display.get_surface()

    def create_tips_glossary_entry(self, unit_name: str, tips_content: str) -> Optional[GlossaryEntry]:
        """Create a tips glossary entry using the positioning system."""
        if self.manager is None:
            return None
            
        # Check if tips entry already exists
        tips_title = f"{unit_name} Tips"
        existing_entry = self._find_existing_glossary_entry(tips_title)
        if existing_entry is not None:
            self.bring_card_to_front(existing_entry)
            return existing_entry
            
        position = self.get_next_card_position()
        
        new_entry = GlossaryEntry(
            manager=self.manager,
            position=position,
            title=tips_title,
            content=tips_content
        )
        
        if info_mode_manager.info_mode:
            card_index = self._get_next_card_index()
            new_entry.creation_index = card_index
            self.glossary_entries.append(new_entry)
        else:
            # In normal mode, we should still track tips entries for duplicate detection
            # but they don't need to be in the main list
            card_index = self._get_next_card_index()
            new_entry.creation_index = card_index
            self.glossary_entries.append(new_entry)
        
        return new_entry

    def create_glossary_entry_from_link(self, entry_type_str: str, position_hint: Optional[tuple[int, int]] = None) -> bool:
        """Create a glossary entry from a link click with proper positioning."""
        return self._create_or_focus_glossary_entry(entry_type_str, position_hint)

    def create_unit_card_from_link(self, unit_type_str: str, position_hint: Optional[tuple[int, int]] = None) -> bool:
        """Create a unit card from a link click with proper positioning."""
        return self._create_or_focus_unit_card(unit_type_str, position_hint)

    def get_next_card_position(self) -> tuple[int, int]:
        """Get the next available position for a new card, avoiding overlaps and mouse."""
        card_index = self._get_card_index_for_new_card()
        return self._calculate_position_from_index(card_index)

    def get_card_position_near_mouse(self, mouse_pos: tuple[int, int]) -> tuple[int, int]:
        """Get a card position near the mouse but ensuring it stays on screen."""
        if self.screen is None:
            return mouse_pos
            
        x = max(0, min(mouse_pos[0], self.screen.get_width() - self.CARD_WIDTH))
        y = max(0, min(mouse_pos[1], self.screen.get_height() - self.CARD_HEIGHT))
        return (x, y)

    def update(self, time_delta: float) -> None:
        """Update the unit card animations."""
        if info_mode_manager.info_mode:
            for card in self.unit_cards:
                card.update(time_delta)
        else:
            if self.unit_card is not None:
                # Set time_delta to a fixed value to prevent animation issues
                fixed_time_delta = 1/60  # 60 FPS equivalent
                self.unit_card.update(fixed_time_delta)

    def process_events(self, event: pygame.event.Event) -> bool:
        """Process UI events for unit cards (Tips button, link clicks, etc.)."""
        if info_mode_manager.info_mode:
            for card in self.unit_cards:
                if card.process_event(event):
                    return True
        else:
            if self.unit_card is not None and self.unit_card.process_event(event):
                return True
        
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            return self._handle_link_click(event)
        
        return False

    def _handle_link_click(self, event: pygame.event.Event) -> bool:
        """Handle clicks on links in unit card descriptions."""
        if not hasattr(event, 'link_target'):
            return False
            
        link_target = event.link_target
        mouse_pos = pygame.mouse.get_pos()
        
        if self._is_unit_type(link_target):
            return self._create_or_focus_unit_card(link_target, mouse_pos)
        else:
            return self._create_or_focus_glossary_entry(link_target, mouse_pos)

    def _is_unit_type(self, type_str: str) -> bool:
        """Check if a string represents a valid unit type."""
        for unit_type in UnitType:
            if unit_type.value == type_str:
                return True
        return False

    def _create_or_focus_unit_card(self, unit_type_str: str, position_hint: Optional[tuple[int, int]] = None) -> bool:
        """Create a new unit card or bring existing one to front."""
        target_unit_type = None
        for unit_type in UnitType:
            if unit_type.value == unit_type_str:
                target_unit_type = unit_type
                break
                
        if target_unit_type is None:
            return False
        
        self._cleanup_dead_cards()
        
        existing_card = self._find_existing_unit_card(target_unit_type)
        if existing_card is not None:
            self.bring_card_to_front(existing_card)
            return True
        
        if position_hint and not info_mode_manager.info_mode:
            position = self.get_card_position_near_mouse(position_hint)
            card_index = None
        else:
            card_index = self._get_card_index_for_new_card()
            position = self._calculate_position_from_index(card_index)
        
        new_card = self._create_unit_card(target_unit_type, position)
        
        if info_mode_manager.info_mode:
            new_card.creation_index = card_index if card_index is not None else self._get_next_card_index()
            self.unit_cards.append(new_card)
        else:
            if self.unit_card is not None:
                self.unit_card.kill()
            self.unit_card = new_card
            if card_index is not None:
                new_card.creation_index = card_index
            
        return True

    def _create_or_focus_glossary_entry(self, entry_type_str: str, position_hint: Optional[tuple[int, int]] = None) -> bool:
        """Create a new glossary entry or bring existing one to front."""
        # Import here to avoid circular imports
        from ui_components.game_data import GlossaryEntryType, GLOSSARY_ENTRIES
        
        entry_type = None
        for glossary_type in GlossaryEntryType:
            if glossary_type.value == entry_type_str:
                entry_type = glossary_type
                break
                
        if entry_type is None:
            return False
            
        if entry_type not in GLOSSARY_ENTRIES:
            return False
            
        self._cleanup_dead_cards()
        
        existing_entry = self._find_existing_glossary_entry(entry_type_str)
        if existing_entry is not None:
            self.bring_card_to_front(existing_entry)
            return True
        
        if position_hint and not info_mode_manager.info_mode:
            position = self.get_card_position_near_mouse(position_hint)
            card_index = None
        else:
            card_index = self._get_card_index_for_new_card()
            position = self._calculate_position_from_index(card_index)
        
        entry_data = GLOSSARY_ENTRIES[entry_type]
        new_entry = GlossaryEntry(
            manager=self.manager,
            position=position,
            title=entry_type.value,
            content=entry_data
        )
        
        if info_mode_manager.info_mode:
            new_entry.creation_index = card_index if card_index is not None else self._get_next_card_index()
            self.glossary_entries.append(new_entry)
        else:
            # In normal mode, just create the entry at the calculated position
            if card_index is not None:
                new_entry.creation_index = card_index
            
        return True

    def _get_card_index_for_new_card(self) -> int:
        """Get the index where a new card should be placed, considering mouse collision."""
        if info_mode_manager.info_mode:
            self._cleanup_dead_cards()
            intended_index = self._get_next_card_index()
        else:
            intended_index = 0
        
        return self._adjust_index_for_mouse_collision(intended_index)

    def _adjust_index_for_mouse_collision(self, intended_index: int) -> int:
        """Adjust the index if mouse is in the way."""
        position = self._calculate_position_from_index(intended_index)
        mouse_pos = pygame.mouse.get_pos()
        
        if self._is_mouse_in_card_area(mouse_pos, position):
            return intended_index + 1
        else:
            return intended_index

    def _calculate_position_from_index(self, card_index: int) -> tuple[int, int]:
        """Calculate position from card index using the grid system."""
        available_width = self.screen.get_width() - 2 * self.MARGIN
        cards_per_row = max(1, available_width // (self.CARD_WIDTH + self.CARD_SPACING))
        
        return self._calculate_card_position(card_index, cards_per_row)

    def _calculate_card_position(self, card_index: int, cards_per_row: int) -> tuple[int, int]:
        """Calculate the position for a card at the given index."""
        row = card_index // cards_per_row
        col = card_index % cards_per_row
        
        # Calculate base position for first row (centered vertically)
        base_y = (self.screen.get_height() - self.CARD_HEIGHT) // 2
        
        # Calculate x position - start from left and work right, with additional right offset per row
        x = self.MARGIN + col * (self.CARD_WIDTH + self.CARD_SPACING) + row * self.ROW_OFFSET
        
        # Calculate y position - stack rows slightly below for layered effect
        y = base_y + row * self.ROW_OFFSET
        
        return (x, y)
    
    def _is_mouse_in_card_area(self, mouse_pos: tuple[int, int], card_pos: tuple[int, int]) -> bool:
        """Check if the mouse position overlaps with the card area."""
        mouse_x, mouse_y = mouse_pos
        card_x, card_y = card_pos
        
        return (card_x <= mouse_x <= card_x + self.CARD_WIDTH and 
                card_y <= mouse_y <= card_y + self.CARD_HEIGHT)

    def _cleanup_dead_cards(self) -> None:
        """Remove any dead cards from the unit_cards and glossary_entries lists."""
        self.unit_cards = [card for card in self.unit_cards if card.window.alive()]
        self.glossary_entries = [entry for entry in self.glossary_entries if entry.window.alive()]

    def _get_next_card_index(self) -> int:
        """Get the next available index that doesn't overlap existing cards or mouse."""
        existing_indices = set()
        
        # Collect indices from both unit cards and glossary entries
        for card in self.unit_cards:
            if hasattr(card, 'creation_index'):
                existing_indices.add(card.creation_index)
        
        for entry in self.glossary_entries:
            if hasattr(entry, 'creation_index'):
                existing_indices.add(entry.creation_index)
        
        max_index = max(existing_indices) if existing_indices else -1
        
        # Try to find a gap in the existing indices
        for potential_index in range(max_index + 2):
            if potential_index not in existing_indices:
                if not self._is_mouse_at_index(potential_index):
                    return potential_index
        
        # No valid gaps found, use next highest index
        next_highest = max_index + 1
        if self._is_mouse_at_index(next_highest):
            return next_highest + 1
        else:
            return next_highest

    def _is_mouse_at_index(self, index: int) -> bool:
        """Check if the mouse is positioned over the given index location."""
        position = self._calculate_position_from_index(index)
        mouse_pos = pygame.mouse.get_pos()
        return self._is_mouse_in_card_area(mouse_pos, position)

    def _find_existing_unit_card(self, unit_type: UnitType) -> Optional[UnitCard]:
        """Find an existing unit card of the given type."""
        for card in self.unit_cards:
            if card.unit_type == unit_type:
                return card
        return None

    def _find_existing_glossary_entry(self, entry_title: str) -> Optional[GlossaryEntry]:
        """Find an existing glossary entry with the given title."""
        for entry in self.glossary_entries:
            if entry.title == entry_title:
                return entry
        return None

    def _create_glossary_entry_from_link(self, entry_type_str: str, click_position: tuple[int, int]) -> bool:
        """Create a glossary entry from a link click."""
        return self._create_or_focus_glossary_entry(entry_type_str, click_position)

    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        return self._selected_unit_type
    
    @selected_unit_type.setter
    def selected_unit_type(self, value: Optional[UnitType]) -> None:
        if self._selected_unit_type != value:
            if not info_mode_manager.info_mode:
                self._hide_stats()
            self._selected_unit_type = value
            self._show_stats()

    def _show_stats(self) -> None:
        """Show the unit card for a unit type."""
        if self.manager is None or self.screen is None:
            return
        if self._selected_unit_type is None:
            return
        
        self._create_or_focus_unit_card(self._selected_unit_type.value)

    def _hide_stats(self) -> None:
        """Hide the unit card(s) if they exist."""
        if info_mode_manager.info_mode:
            pass
        else:
            if self.unit_card is not None:
                self.unit_card.kill()
                self.unit_card = None

    def bring_card_to_front(self, card: Union[UnitCard, GlossaryEntry]) -> None:
        """Bring a specific unit card or glossary entry to the front."""
        if card.window.alive():
            card.bring_to_front()

    def bring_card_to_front_by_index(self, index: int) -> None:
        """Bring a unit card to the front by its index in the info mode list."""
        if info_mode_manager.info_mode:
            all_cards = self.unit_cards + self.glossary_entries
            if 0 <= index < len(all_cards):
                self.bring_card_to_front(all_cards[index])
        elif not info_mode_manager.info_mode and index == 0 and self.unit_card:
            self.bring_card_to_front(self.unit_card)

    def clear_all_cards(self) -> None:
        """Clear all cards (used when exiting info mode)."""
        if self.unit_card is not None:
            self.unit_card.kill()
            self.unit_card = None
            
        for card in self.unit_cards:
            card.kill()
        self.unit_cards.clear()
        
        for entry in self.glossary_entries:
            entry.kill()
        self.glossary_entries.clear()

    def _create_unit_card(self, unit_type: UnitType, position: tuple[int, int]) -> UnitCard:
        """Create a unit card with all stats populated."""
        unit_data = UNIT_DATA[unit_type]
        
        new_card = UnitCard(
            screen=self.screen,
            manager=self.manager,
            position=position,
            name=unit_data["name"],
            description=unit_data["description"],
            unit_type=unit_type
        )
        
        for stat_type in StatType:
            if stat_type in unit_data["stats"]:
                new_card.add_stat(
                    stat_type=stat_type,
                    value=unit_data["stats"][stat_type],
                    tooltip_text=unit_data["tooltips"][stat_type]
                )
            else:
                new_card.skip_stat(stat_type=stat_type)
        
        return new_card

selected_unit_manager = SelectedUnitManager()