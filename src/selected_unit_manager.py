"""Service for managing the stats card UI."""
from typing import Optional, List, Tuple, Union
import pygame
import pygame_gui

from components.unit_type import UnitType
from components.unit_tier import UnitTier
from components.item import ItemType
from components.spell_type import SpellType
from ui_components.unit_card import UnitCard
from ui_components.item_card import ItemCard
from ui_components.spell_card import SpellCard
from ui_components.glossary_entry import GlossaryEntry
from ui_components.game_data import get_unit_data, get_item_data, UnitTier, StatType, GLOSSARY_ENTRIES
from info_mode_manager import info_mode_manager
from progress_manager import progress_manager

class SelectedUnitManager:
    """Service for managing the stats card UI."""

    CARD_WIDTH = 300
    CARD_HEIGHT = 475
    CARD_SPACING = 10
    MARGIN = 20
    ROW_OFFSET = 20  # Offset for layered effect

    def __init__(self):
        """Initialize the stats card manager."""
        self.cards: List[Union[UnitCard, ItemCard, SpellCard, GlossaryEntry]] = []  # Unified list for all cards
        self._selected_unit_type: Optional[UnitType] = None
        self._selected_unit_tier: Optional[UnitTier] = None
        self._selected_item_type: Optional[ItemType] = None
        self._selected_spell_type: Optional[SpellType] = None
        self._selected_items: List[ItemType] = []
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
            screen=self.screen,
            manager=self.manager,
            position=position,
            title=tips_title,
            content=tips_content
        )
        
        card_index = self._get_next_card_index()
        new_entry.creation_index = card_index
        self.cards.append(new_entry)
        
        return new_entry

    def create_glossary_entry_from_link(self, entry_type_str: str) -> bool:
        """Create a glossary entry from a link click with proper positioning."""
        return self._create_or_focus_glossary_entry(entry_type_str)

    def create_unit_card_from_link(self, unit_type_str: str, unit_tier: UnitTier) -> bool:
        """Create a unit card from a link click with proper positioning."""
        return self._create_or_focus_unit_card(unit_type_str, unit_tier)

    def create_item_card_from_link(self, item_type: ItemType) -> bool:
        """Create an item card from a link click with proper positioning."""
        return self._create_or_focus_item_card(item_type)

    def create_spell_card_from_link(self, spell_type: SpellType) -> bool:
        """Create a spell card from a link click with proper positioning."""
        return self._create_or_focus_spell_card(spell_type)

    def get_next_card_position(self) -> tuple[int, int]:
        """Get the next available position for a new card, avoiding overlaps and mouse."""
        card_index = self._get_card_index_for_new_card()
        return self._calculate_position_from_index(card_index)

    def update(self, time_delta: float) -> None:
        """Update the unit card animations and flash effects."""
        # Set time_delta to a fixed value to prevent animation issues
        fixed_time_delta = 1/30  # 30 FPS equivalent
        
        if info_mode_manager.info_mode:
            for card in self.cards:
                card.update(time_delta)
        else:
            for card in self.cards:
                card.update(fixed_time_delta)

    def process_events(self, event: pygame.event.Event) -> bool:
        """Process UI events for unit cards (Tips button, link clicks, etc.)."""
        for card in self.cards:
            if hasattr(card, 'process_event') and card.process_event(event):
                return True
        
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            return self._handle_link_click(event)
        
        return False

    def _handle_link_click(self, event: pygame.event.Event) -> bool:
        """Handle clicks on links in unit card descriptions."""
        if not hasattr(event, 'link_target'):
            return False
            
        link_target = event.link_target
        
        if self._is_unit_type(link_target):
            # For link clicks, use the tier from progress manager
            target_unit_type = None
            for unit_type in UnitType:
                if unit_type.value == link_target:
                    target_unit_type = unit_type
                    break
            if target_unit_type is None:
                return False
            unit_tier = progress_manager.get_unit_tier(target_unit_type)
            return self._create_or_focus_unit_card(link_target, unit_tier)
        else:
            return self._create_or_focus_glossary_entry(link_target)

    def _is_unit_type(self, type_str: str) -> bool:
        """Check if a string represents a valid unit type."""
        for unit_type in UnitType:
            if unit_type.value == type_str:
                return True
        return False

    def _create_or_focus_unit_card(self, unit_type_str: str, unit_tier: UnitTier) -> bool:
        """Create a new unit card or bring existing one to front."""
        target_unit_type = None
        for unit_type in UnitType:
            if unit_type.value == unit_type_str:
                target_unit_type = unit_type
                break
                
        if target_unit_type is None:
            return False
        
        self._cleanup_dead_cards()
        
        existing_card = self._find_existing_unit_card(target_unit_type, unit_tier)
        if existing_card is not None:
            self.bring_card_to_front(existing_card)
            return True
        
        card_index = self._get_card_index_for_new_card()
        position = self._calculate_position_from_index(card_index)
        
        new_card = self._create_unit_card(target_unit_type, position, unit_tier)
        
        new_card.creation_index = card_index
        self.cards.append(new_card)
            
        return True

    def _create_or_focus_glossary_entry(self, entry_type_str: str) -> bool:
        """Create a new glossary entry or bring existing one to front."""
        # Import here to avoid circular imports
        from ui_components.game_data import GlossaryEntryType
        
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
        
        card_index = self._get_card_index_for_new_card()
        position = self._calculate_position_from_index(card_index)
        
        entry_data = GLOSSARY_ENTRIES[entry_type]
        new_entry = GlossaryEntry(
            screen=self.screen,
            manager=self.manager,
            position=position,
            title=entry_type.value,
            content=entry_data
        )
        new_entry.creation_index = card_index
        self.cards.append(new_entry)
            
        return True

    def _get_card_index_for_new_card(self) -> int:
        """Get the index where a new card should be placed, considering mouse collision."""
        self._cleanup_dead_cards()
        intended_index = self._get_next_card_index()
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

    def _create_or_focus_item_card(self, item_type: ItemType) -> bool:
        """Create a new item card or bring existing one to front."""
        self._cleanup_dead_cards()
        
        existing_card = self._find_existing_item_card(item_type)
        if existing_card is not None:
            self.bring_card_to_front(existing_card)
            return True
        
        card_index = self._get_card_index_for_new_card()
        position = self._calculate_position_from_index(card_index)
        
        new_card = self._create_item_card(item_type, position)
        
        new_card.creation_index = card_index
        self.cards.append(new_card)
            
        return True

    def _cleanup_dead_cards(self) -> None:
        """Remove any dead cards from the cards list."""
        self.cards = [card for card in self.cards if self._is_card_alive(card)]
    
    def _is_card_alive(self, card) -> bool:
        """Check if a card is still alive (not killed)."""
        if hasattr(card, 'window') and card.window is not None:
            return card.window.alive()
        elif hasattr(card, 'card_container') and card.card_container is not None:
            return card.card_container.alive()
        else:
            return True  # Assume alive if we can't determine

    def _get_next_card_index(self) -> int:
        """Get the next available index that doesn't overlap existing cards or mouse."""
        existing_indices = set()
        
        # Collect indices from all cards
        for card in self.cards:
            if hasattr(card, 'creation_index'):
                existing_indices.add(card.creation_index)
        
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

    def _find_existing_unit_card(self, unit_type: UnitType, unit_tier: UnitTier) -> Optional[UnitCard]:
        """Find an existing unit card of the given type and tier."""
        for card in self.cards:
            if isinstance(card, UnitCard) and card.unit_type == unit_type and card.unit_tier == unit_tier:
                return card
        return None

    def _find_existing_glossary_entry(self, entry_title: str) -> Optional[GlossaryEntry]:
        """Find an existing glossary entry with the given title."""
        for card in self.cards:
            if isinstance(card, GlossaryEntry) and card.title == entry_title:
                return card
        return None

    def _find_existing_item_card(self, item_type: ItemType) -> Optional[ItemCard]:
        """Find an existing item card of the given type."""
        for card in self.cards:
            if isinstance(card, ItemCard) and card.item_type == item_type:
                return card
        return None

    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        return self._selected_unit_type
    
    @selected_unit_type.setter
    def selected_unit_type(self, value: Optional[UnitType]) -> None:
        if self._selected_unit_type != value:
            if not info_mode_manager.info_mode:
                self._hide_stats()
            self._selected_unit_type = value
            # Reset tier to None when unit type changes
            self._selected_unit_tier = None
            self._show_stats()

    @property
    def selected_unit_tier(self) -> Optional[UnitTier]:
        return self._selected_unit_tier
    
    @selected_unit_tier.setter
    def selected_unit_tier(self, value: Optional[UnitTier]) -> None:
        if self._selected_unit_tier != value:
            if not info_mode_manager.info_mode:
                self._hide_stats()
            self._selected_unit_tier = value
            self._show_stats()

    @property
    def selected_item_type(self) -> Optional[ItemType]:
        return self._selected_item_type
    
    @selected_item_type.setter
    def selected_item_type(self, value: Optional[ItemType]) -> None:
        if self._selected_item_type != value:
            if not info_mode_manager.info_mode:
                self._hide_stats()
            self._selected_item_type = value
            self._show_stats()

    def set_selected_unit(self, unit_type: Optional[UnitType], unit_tier: Optional[UnitTier] = None, items: Optional[List[ItemType]] = None) -> None:
        """Set the selected unit type, tier, and items at once."""
        if self._selected_unit_type != unit_type or self._selected_unit_tier != unit_tier or self._selected_items != (items or []):
            if not info_mode_manager.info_mode:
                self._hide_stats()
            self._selected_unit_type = unit_type
            self._selected_unit_tier = unit_tier
            self._selected_items = items or []
            self._show_stats()

    def _show_stats(self) -> None:
        """Show the unit card for a unit type."""
        if self.manager is None or self.screen is None:
            return
        if self._selected_unit_type is None:
            return
        
        # Determine the tier to use
        if self._selected_unit_tier is not None:
            # Use the explicitly set tier (for units on battlefield)
            unit_tier = self._selected_unit_tier
        else:
            # Use the tier from progress manager (for barracks buttons)
            unit_tier = progress_manager.get_unit_tier(self._selected_unit_type)
        
        self._create_or_focus_unit_card(self._selected_unit_type.value, unit_tier)
        
        # Also create item cards for unique item types
        unique_item_types = sorted(list(set(self._selected_items)), key=lambda x: self._selected_items.index(x))
        for item_type in unique_item_types:
            self._create_or_focus_item_card(item_type)

    def _hide_stats(self) -> None:
        """Hide all cards if they exist."""
        if info_mode_manager.info_mode:
            pass
        else:
            # Kill all cards
            for card in self.cards:
                if self._is_card_alive(card):
                    card.kill()
            self.cards.clear()

    def bring_card_to_front(self, card: Union[UnitCard, ItemCard, SpellCard, GlossaryEntry]) -> None:
        """Bring a specific unit card, item card, spell card, or glossary entry to the front."""
        if hasattr(card, 'window') and card.window is not None and card.window.alive():
            card.bring_to_front()
        elif hasattr(card, 'card_container') and card.card_container is not None and card.card_container.alive():
            # For cards using containers, try to bring the container to front if possible
            if hasattr(card.card_container, 'bring_to_front'):
                card.card_container.bring_to_front()

    def bring_card_to_front_by_index(self, index: int) -> None:
        """Bring a card to the front by its index in the cards list."""
        if 0 <= index < len(self.cards):
            self.bring_card_to_front(self.cards[index])

    def clear_all_cards(self) -> None:
        """Clear all cards."""
        for card in self.cards:
            card.kill()
        self.cards.clear()

    def _create_unit_card(self, unit_type: UnitType, position: Tuple[float, float], unit_tier: UnitTier) -> UnitCard:
        """Create a unit card with all stats populated."""
        unit_data = get_unit_data(unit_type, unit_tier)
        
        new_card = UnitCard(
            screen=self.screen,
            manager=self.manager,
            position=position,
            name=unit_data.name,
            description=unit_data.description,
            unit_type=unit_type,
            unit_tier=unit_tier,
            container=None
        )
        
        for stat_type in StatType:
            stat_value = unit_data.stats[stat_type]
            if stat_value is not None:
                new_card.add_stat(
                    stat_type=stat_type,
                    value=int(stat_value),
                    tooltip_text=unit_data.tooltips[stat_type] or "N/A",
                    modification_level=unit_data.modification_levels.get(stat_type, 0)
                )
            else:
                new_card.skip_stat(stat_type=stat_type)
        
        return new_card

    def set_selected_item(self, item_type: Optional[ItemType]) -> None:
        """Set the selected item type and create/update the item card."""
        if self.manager is None or self.screen is None:
            return
            
        self._selected_item_type = item_type
        
        if item_type is None:
            # Clear item cards
            if not info_mode_manager.info_mode:
                item_cards_to_remove = [card for card in self.cards if isinstance(card, ItemCard)]
                for card in item_cards_to_remove:
                    card.kill()
                    self.cards.remove(card)
        else:
            # Use the standardized create or focus method
            self._create_or_focus_item_card(item_type)

    def _create_item_card(self, item_type: ItemType, position: Tuple[float, float]) -> ItemCard:
        """Create an item card with all information populated."""
        return ItemCard(
            screen=self.screen,
            manager=self.manager,
            position=position,
            item_type=item_type,
            container=None
        )

    def _find_existing_spell_card(self, spell_type: SpellType) -> Optional[SpellCard]:
        """Find an existing spell card for the given spell type."""
        for card in self.cards:
            if isinstance(card, SpellCard) and card.spell_type == spell_type:
                return card
        return None

    def _create_or_focus_spell_card(self, spell_type: SpellType) -> bool:
        """Create a new spell card or bring existing one to front."""
        self._cleanup_dead_cards()
        
        existing_card = self._find_existing_spell_card(spell_type)
        if existing_card is not None:
            self.bring_card_to_front(existing_card)
            return True
        
        card_index = self._get_card_index_for_new_card()
        position = self._calculate_position_from_index(card_index)
        
        new_card = self._create_spell_card(spell_type, position)
        
        new_card.creation_index = card_index
        self.cards.append(new_card)
            
        return True

    def _create_spell_card(self, spell_type: SpellType, position: Tuple[float, float]) -> SpellCard:
        """Create a spell card with all information populated."""
        return SpellCard(
            screen=self.screen,
            manager=self.manager,
            position=position,
            spell_type=spell_type,
            container=None
        )

    def set_selected_spell_type(self, spell_type: Optional[SpellType]) -> None:
        """Set the selected spell type and create/update the spell card."""
        if self.manager is None or self.screen is None:
            return
            
        self._selected_spell_type = spell_type
        
        if spell_type is None:
            # Clear spell cards
            if not info_mode_manager.info_mode:
                spell_cards_to_remove = [card for card in self.cards if isinstance(card, SpellCard)]
                for card in spell_cards_to_remove:
                    card.kill()
                    self.cards.remove(card)
        else:
            # Use the standardized create or focus method
            self._create_or_focus_spell_card(spell_type)

selected_unit_manager = SelectedUnitManager()