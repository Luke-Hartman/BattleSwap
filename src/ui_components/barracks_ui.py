"""Provides the BarracksUI component for managing available units and items."""
import time
from typing import Dict, List, Optional, Union, Tuple
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel, UIScrollingContainer, UIButton, UILabel, UITabContainer

import battles
from components.unit_type import UnitType
from entities.units import unit_theme_ids, Faction
from entities.items import ItemType
from components.spell_type import SpellType
from selected_unit_manager import selected_unit_manager
from progress_manager import progress_manager
from point_values import unit_values, item_values, spell_values
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from keyboard_shortcuts import format_button_text
from ui_components.unit_count import UnitCount
from ui_components.item_count import ItemCount
from ui_components.spell_count import SpellCount


class BarracksUI(UITabContainer):
    """UI component for managing available units and items in the barracks."""

    def __init__(
            self,
            manager: pygame_gui.UIManager,
            starting_units: Dict[UnitType, int],
            acquired_items: Dict[ItemType, int],
            acquired_spells: Dict[SpellType, int],
            interactive: bool,
            sandbox_mode: bool,
            current_battle: Optional[battles.Battle] = None,
    ):
        self.manager = manager
        self._units = starting_units.copy()
        self._items = acquired_items.copy()
        self._spells = acquired_spells.copy()
        self.interactive = interactive
        self.sandbox_mode = sandbox_mode
        self.current_battle = current_battle
        self.selected_unit_type: Optional[UnitType] = None
        self.selected_item_type: Optional[ItemType] = None
        self.selected_spell_type: Optional[SpellType] = None
        
        # Initialize units
        if sandbox_mode:
            self._units = {unit_type: float('inf') for unit_type in UnitType}
            encountered_units = set(UnitType)
        else:
            encountered_units = set(starting_units.keys())
            for hex_coords in progress_manager.solutions:
                battle = battles.get_battle_coords(hex_coords)
                for enemy_type, _, _ in battle.enemies:
                    encountered_units.add(enemy_type)

            for unit_type in encountered_units:
                if unit_type not in self._units:
                    self._units[unit_type] = 0
        
        # Initialize items
        if sandbox_mode:
            self._items = {item_type: float('inf') for item_type in ItemType}
        else:
            # Include all items that have been acquired (have entries in progress manager) even if 0 copies
            acquired_item_types = set(progress_manager.acquired_items.keys())
            for item_type in acquired_item_types:
                if item_type not in self._items:
                    self._items[item_type] = 0
        
        # Initialize spells
        if sandbox_mode:
            self._spells = {spell_type: float('inf') for spell_type in SpellType}
        else:
            # Include all spells that have been acquired (have entries in progress manager) even if 0 copies
            acquired_spell_types = set(progress_manager.acquired_spells.keys())
            for spell_type in acquired_spell_types:
                if spell_type not in self._spells:
                    self._spells[spell_type] = 0
        
        self.available_factions = {
            Faction.faction_of(unit_type)
            for unit_type in encountered_units
        }
        
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding - 220
        padding = 10
        
        needs_scrollbar, content_height = self._calculate_panel_dimensions(panel_width, "ALL")
        
        super().__init__(
            relative_rect=pygame.Rect(
                (side_padding, pygame.display.Info().current_h - content_height - 10 - 30),
                (panel_width, content_height + 30)
            ),
            manager=manager,
        )

        # Create tabs
        all_tab_index = self.add_tab("ALL", "all_tab")
        self.all_tab_index = all_tab_index
        
        self.faction_to_tab_index: Dict[Faction, int] = {}
        for faction in sorted(self.available_factions, key=lambda f: f.value):
            tab_index = self.add_tab(faction.name, "faction_tab")
            self.faction_to_tab_index[faction] = tab_index
        
        # Only show items/spells tabs if they have been acquired
        self.items_tab_index = None
        self.spells_tab_index = None
        
        if self._has_acquired_items():
            items_tab_index = self.add_tab("ITEMS", "items_tab")
            self.items_tab_index = items_tab_index
        
        if self._has_acquired_spells():
            spells_tab_index = self.add_tab("SPELLS", "spells_tab")
            self.spells_tab_index = spells_tab_index
        
        # Unified container system
        self.containers: Dict[str, UIScrollingContainer] = {}
        self.entity_items: Dict[str, List[Union[UnitCount, ItemCount, SpellCount]]] = {
            "ALL": [],
            "ITEMS": [],
            "SPELLS": []
        }
        
        # Add faction containers
        for faction in self.available_factions:
            self.entity_items[faction.name] = []

        # Create all containers
        self._create_containers(padding, panel_width, content_height)
        
        self._populate_entities(padding, needs_scrollbar)

        # Set "ALL" tab as default
        self.switch_current_container(all_tab_index)
    
    def _has_acquired_items(self) -> bool:
        """Check if any items have been acquired (count > 0)."""
        if self.sandbox_mode:
            return True  # Always show in sandbox mode
        return any(count > 0 for count in self._items.values())
    
    def _has_acquired_spells(self) -> bool:
        """Check if any spells have been acquired (count > 0)."""
        if self.sandbox_mode:
            return True  # Always show in sandbox mode
        return any(count > 0 for count in self._spells.values())

    def _create_containers(self, padding: int, panel_width: int, content_height: int) -> None:
        """Create all tab containers."""
        container_rect = pygame.Rect(
            (padding, padding),
            (panel_width - 2 * padding, content_height - 2 * padding)
        )
        
        # Create ALL tab container
        all_tab_panel = self.get_tab_container(self.all_tab_index)
        all_container = UIScrollingContainer(
            relative_rect=container_rect,
            manager=self.manager,
            container=all_tab_panel,
            allow_scroll_y=False,
        )
        self.containers["ALL"] = all_container
        
        # Create faction tab containers
        for faction in self.available_factions:
            tab_index = self.faction_to_tab_index[faction]
            tab_panel = self.get_tab_container(tab_index)
            container = UIScrollingContainer(
                relative_rect=container_rect,
                manager=self.manager,
                container=tab_panel,
                allow_scroll_y=False,
            )
            self.containers[faction.name] = container
        
        # Create ITEMS tab container (only if tab exists)
        if self.items_tab_index is not None:
            items_tab_panel = self.get_tab_container(self.items_tab_index)
            items_container = UIScrollingContainer(
                relative_rect=container_rect,
                manager=self.manager,
                container=items_tab_panel,
                allow_scroll_y=False,
            )
            self.containers["ITEMS"] = items_container
        
        # Create SPELLS tab container (only if tab exists)
        if self.spells_tab_index is not None:
            spells_tab_panel = self.get_tab_container(self.spells_tab_index)
            spells_container = UIScrollingContainer(
                relative_rect=container_rect,
                manager=self.manager,
                container=spells_tab_panel,
                allow_scroll_y=False,
            )
            self.containers["SPELLS"] = spells_container

    def _calculate_panel_dimensions(self, panel_width: int, tab_name: str = "ALL") -> tuple[bool, int]:
        """Calculate panel dimensions based on content for the given tab."""
        padding = 10
        
        if tab_name == "ALL":
            # ALL tab: units, items, and spells with count > 0
            units_count = len([unit_type for unit_type, count in self._units.items() 
                              if count > 0 or self.sandbox_mode])
            items_count = len([item_type for item_type, count in self._items.items() 
                              if count > 0 or self.sandbox_mode])
            spells_count = len([spell_type for spell_type, count in self._spells.items() 
                               if count > 0 or self.sandbox_mode])
            total_count = units_count + items_count + spells_count
        elif tab_name == "ITEMS":
            # ITEMS tab: all items regardless of count
            total_count = len(ItemType)
        elif tab_name == "SPELLS":
            # SPELLS tab: all spells regardless of count
            total_count = len(SpellType)
        else:
            # Faction tab: all units in faction regardless of count
            faction = next((f for f in self.available_factions if f.name == tab_name), None)
            if faction:
                total_count = len(Faction.units(faction))
            else:
                total_count = 0
        
        # All entities use the same size (UnitCount.size == ItemCount.size)
        total_width = total_count * (UnitCount.size + padding // 2) - padding // 2 if total_count > 0 else 0
        needs_scrollbar = total_width > panel_width - 2 * padding
        panel_height = UnitCount.size + 45 if needs_scrollbar else UnitCount.size + 20

        return needs_scrollbar, panel_height

    def _populate_entities(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate all tabs with their respective entities."""
        # Populate ALL tab - units and items with count > 0
        self._populate_all_tab(padding, needs_scrollbar)
        
        # Populate faction tabs - all units in each faction
        self._populate_faction_tabs(padding, needs_scrollbar)
        
        # Populate ITEMS tab - only if tab exists
        if self.items_tab_index is not None:
            self._populate_items_tab(padding, needs_scrollbar)
        
        # Populate SPELLS tab - only if tab exists
        if self.spells_tab_index is not None:
            self._populate_spells_tab(padding, needs_scrollbar)

    def _populate_all_tab(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate the ALL tab with units and items that have count > 0."""
        container = self.containers["ALL"]
        container_height = container.rect.height
        y_offset = (container_height - UnitCount.size) // 2 if not needs_scrollbar else 0
        
        x_position = 0
        index = 0
        
        # Add units with count > 0
        available_units = sorted(
            [(unit_type, count) for unit_type, count in self._units.items() 
             if count > 0 or self.sandbox_mode],
            key=lambda x: x[0].value
        )
        
        for unit_type, count in available_units:
            hotkey = str((index + 1) % 10) if index < 10 else None
            item = UnitCount(
                x_pos=x_position,
                y_pos=y_offset,
                unit_type=unit_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=container,
                infinite=self.sandbox_mode,
                hotkey=hotkey
            )
            
            if index < 10:
                shortcut_key = str((index + 1) % 10)
                unit_name = unit_type.value.replace('_', ' ').title()
                tooltip_text = format_button_text(unit_name, shortcut_key)
                item.button.tool_tip_text = tooltip_text
                item.button.tool_tip_delay = 0
            
            self.entity_items["ALL"].append(item)
            x_position += item.size + padding // 2
            index += 1
        
        # Add items with count > 0
        available_items = sorted(
            [(item_type, count) for item_type, count in self._items.items() 
             if count > 0 or self.sandbox_mode],
            key=lambda x: x[0].value
        )
        
        for item_type, count in available_items:
            hotkey = str((index + 1) % 10) if index < 10 else None
            item_count = ItemCount(
                x_pos=x_position,
                y_pos=y_offset,
                item_type=item_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=container,
                infinite=self.sandbox_mode,
                hotkey=hotkey
            )
            
            if index < 10:
                shortcut_key = str((index + 1) % 10)
                item_name = item_type.value.replace('_', ' ').title()
                tooltip_text = format_button_text(item_name, shortcut_key)
                item_count.button.tool_tip_text = tooltip_text
                item_count.button.tool_tip_delay = 0
            
            self.entity_items["ALL"].append(item_count)
            x_position += item_count.size + padding // 2
            index += 1
        
        # Add spells with count > 0
        available_spells = sorted(
            [(spell_type, count) for spell_type, count in self._spells.items() 
             if count > 0 or self.sandbox_mode],
            key=lambda x: x[0].value
        )
        
        for spell_type, count in available_spells:
            hotkey = str((index + 1) % 10) if index < 10 else None
            spell_count = SpellCount(
                x_pos=x_position,
                y_pos=y_offset,
                spell_type=spell_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=container,
                infinite=self.sandbox_mode,
                hotkey=hotkey
            )
            
            if index < 10:
                shortcut_key = str((index + 1) % 10)
                spell_name = spell_type.value.replace('_', ' ').title()
                tooltip_text = format_button_text(spell_name, shortcut_key)
                spell_count.button.tool_tip_text = tooltip_text
                spell_count.button.tool_tip_delay = 0
            
            self.entity_items["ALL"].append(spell_count)
            x_position += spell_count.size + padding // 2
            index += 1

    def _populate_faction_tabs(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate faction tabs with all units in each faction."""
        for faction in self.available_factions:
            container = self.containers[faction.name]
            container_height = container.rect.height
            y_offset = (container_height - UnitCount.size) // 2 if not needs_scrollbar else 0
            
            x_position = 0
            faction_units = sorted(
                [(unit_type, count) for unit_type, count in self._units.items() 
                 if Faction.faction_of(unit_type) == faction],
                key=lambda x: x[0].value
            )
            
            for unit_index, (unit_type, count) in enumerate(faction_units):
                hotkey = str((unit_index + 1) % 10) if unit_index < 10 else None
                item = UnitCount(
                    x_pos=x_position,
                    y_pos=y_offset,
                    unit_type=unit_type,
                    count=count,
                    interactive=self.interactive and count > 0,
                    manager=self.manager,
                    container=container,
                    infinite=self.sandbox_mode,
                    hotkey=hotkey
                )
                
                if unit_index < 10:
                    shortcut_key = str((unit_index + 1) % 10)
                    unit_name = unit_type.value.replace('_', ' ').title()
                    tooltip_text = format_button_text(unit_name, shortcut_key)
                    item.button.tool_tip_text = tooltip_text
                    item.button.tool_tip_delay = 0
                
                self.entity_items[faction.name].append(item)
                x_position += item.size + padding // 2

    def _populate_items_tab(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate the ITEMS tab with items that have been acquired ever."""
        container = self.containers["ITEMS"]
        container_height = container.rect.height
        y_offset = (container_height - ItemCount.size) // 2 if not needs_scrollbar else 0
        
        x_position = 0
        # Show items that have been acquired (have entries in progress manager) or in sandbox mode
        acquired_items = sorted(
            [(item_type, count) for item_type, count in self._items.items() 
             if item_type in progress_manager.acquired_items or self.sandbox_mode],
            key=lambda x: x[0].value
        )
        
        for index, (item_type, count) in enumerate(acquired_items):
            hotkey = str((index + 1) % 10) if index < 10 else None
            item_count = ItemCount(
                x_pos=x_position,
                y_pos=y_offset,
                item_type=item_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=container,
                infinite=self.sandbox_mode,
                hotkey=hotkey
            )
            
            if index < 10:
                shortcut_key = str((index + 1) % 10)
                item_name = item_type.value.replace('_', ' ').title()
                tooltip_text = format_button_text(item_name, shortcut_key)
                item_count.button.tool_tip_text = tooltip_text
                item_count.button.tool_tip_delay = 0
            
            self.entity_items["ITEMS"].append(item_count)
            x_position += item_count.size + padding // 2

    def _populate_spells_tab(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate the SPELLS tab with spells that have been acquired ever."""
        container = self.containers["SPELLS"]
        container_height = container.rect.height
        y_offset = (container_height - SpellCount.size) // 2 if not needs_scrollbar else 0
        
        x_position = 0
        # Show spells that have been acquired (have entries in progress manager) or in sandbox mode
        acquired_spells = sorted(
            [(spell_type, count) for spell_type, count in self._spells.items() 
             if spell_type in progress_manager.acquired_spells or self.sandbox_mode],
            key=lambda x: x[0].value
        )
        
        for index, (spell_type, count) in enumerate(acquired_spells):
            hotkey = str((index + 1) % 10) if index < 10 else None
            spell_count = SpellCount(
                x_pos=x_position,
                y_pos=y_offset,
                spell_type=spell_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=container,
                infinite=self.sandbox_mode,
                hotkey=hotkey
            )
            
            if index < 10:
                shortcut_key = str((index + 1) % 10)
                spell_name = spell_type.value.replace('_', ' ').title()
                tooltip_text = format_button_text(spell_name, shortcut_key)
                spell_count.button.tool_tip_text = tooltip_text
                spell_count.button.tool_tip_delay = 0
            
            self.entity_items["SPELLS"].append(spell_count)
            x_position += spell_count.size + padding // 2

    def _full_rebuild(self) -> None:
        """Completely rebuild the barracks UI (including tabs)."""
        # Store current state
        current_tab_name = self.get_tab(self.current_container_index)["text"] if hasattr(self, 'current_container_index') else "ALL"
        
        # Kill all existing UI elements
        self.kill()
        
        # Recreate the entire barracks UI
        self.__init__(
            manager=self.manager,
            starting_units=self._units,
            acquired_items=self._items,
            acquired_spells=self._spells,
            interactive=self.interactive,
            sandbox_mode=self.sandbox_mode,
            current_battle=self.current_battle
        )
        
        # Try to switch back to the same tab if it still exists
        try:
            if current_tab_name == "ITEMS" and self.items_tab_index is not None:
                self.switch_current_container(self.items_tab_index)
            elif current_tab_name == "SPELLS" and self.spells_tab_index is not None:
                self.switch_current_container(self.spells_tab_index)
            else:
                self.switch_current_container(self.all_tab_index)
        except:
            # Fallback to ALL tab if switching fails
            self.switch_current_container(self.all_tab_index)

    def _rebuild(self) -> None:
        """Rebuild the UI when dimensions or content changes."""
        if not hasattr(self, '_previous_dimensions'):
            self._previous_dimensions = None
            
        # Get the current tab name
        current_tab_name = self.get_tab(self.current_container_index)["text"]
        needs_scrollbar, content_height = self._calculate_panel_dimensions(self.rect.width, current_tab_name)
        current_dimensions = (self.rect.width, content_height)

        # Kill all containers and items
        for container in self.containers.values():
            container.kill()
        for items in self.entity_items.values():
            for item in items:
                item.kill()
            items.clear()
        
        # Recreate all containers
        self._create_containers(10, self.rect.width, content_height)
        
        # Repopulate all entities
        self._populate_entities(10, needs_scrollbar)
        self._previous_dimensions = current_dimensions

    def _update_entity_counts(self) -> None:
        """Update counts for all existing entities without rebuilding."""
        # Update ALL tab
        for item in self.entity_items["ALL"]:
            if isinstance(item, UnitCount):
                unit_type = item.unit_type
                count = self._units[unit_type]
                item.update_count(count)
                item.set_interactive(self.interactive and count > 0)
            elif isinstance(item, ItemCount):
                item_type = item.item_type
                count = self._items[item_type]
                item.update_count(count)
                item.set_interactive(self.interactive and count > 0)
            elif isinstance(item, SpellCount):
                spell_type = item.spell_type
                count = self._spells[spell_type]
                item.update_count(count)
                item.set_interactive(self.interactive and count > 0)
        
        # Update faction tabs
        for faction in self.available_factions:
            for item in self.entity_items[faction.name]:
                if isinstance(item, UnitCount):
                    unit_type = item.unit_type
                    count = self._units[unit_type]
                    item.update_count(count)
                    item.set_interactive(self.interactive and count > 0)
        
        # Update ITEMS tab
        for item in self.entity_items["ITEMS"]:
            if isinstance(item, ItemCount):
                item_type = item.item_type
                count = self._items[item_type]
                item.update_count(count)
                item.set_interactive(self.interactive and count > 0)
        
        # Update SPELLS tab
        for item in self.entity_items["SPELLS"]:
            if isinstance(item, SpellCount):
                spell_type = item.spell_type
                count = self._spells[spell_type]
                item.update_count(count)
                item.set_interactive(self.interactive and count > 0)


    def add_unit(self, unit_type: UnitType) -> None:
        """Add a unit of the specified type to the barracks."""
        self._units[unit_type] += 1
        
        # Check if unit needs to be added to ALL tab (was count 0 before)
        was_zero = self._units[unit_type] == 1 and not self.sandbox_mode
        
        if was_zero:
            # Need to rebuild to add unit to ALL tab
            self._rebuild()
        else:
            # Just update existing counts
            self._update_entity_counts()

    def remove_unit(self, unit_type: UnitType) -> None:
        """Remove a unit of the specified type from the barracks."""
        assert self._units[unit_type] > 0
        self._units[unit_type] -= 1
        
        # Check if unit needs to be removed from ALL tab (count became 0)
        became_zero = self._units[unit_type] == 0 and not self.sandbox_mode
        
        if became_zero:
            # Need to rebuild to remove unit from ALL tab
            self._rebuild()
        else:
            # Just update existing counts
            self._update_entity_counts()

    def select_unit_type(self, unit_type: Optional[UnitType]) -> None:
        """Select a unit type across all tabs."""
        for items in self.entity_items.values():
            for item in items:
                if isinstance(item, UnitCount) and item.unit_type == unit_type:
                    item.button.select()
                elif item.button.is_selected:
                    item.button.unselect()

    def select_item_type(self, item_type: Optional[ItemType]) -> None:
        """Select an item type across all tabs."""
        for items in self.entity_items.values():
            for item in items:
                if isinstance(item, ItemCount) and item.item_type == item_type:
                    item.button.select()
                elif item.button.is_selected:
                    item.button.unselect()

    def select_spell_type(self, spell_type: Optional[SpellType]) -> None:
        """Select a spell type across all tabs."""
        for items in self.entity_items.values():
            for item in items:
                if isinstance(item, SpellCount) and item.spell_type == spell_type:
                    item.button.select()
                elif item.button.is_selected:
                    item.button.unselect()

    @property
    def units(self) -> Dict[UnitType, int]:
        """Get the current unit counts."""
        return self._units.copy()

    @property
    def items(self) -> Dict[ItemType, int]:
        """Get the current item counts."""
        return self._items.copy()

    @property
    def unit_list_items(self) -> List[UnitCount]:
        """Get all unit count items across all tabs."""
        return [item for items in self.entity_items.values() for item in items if isinstance(item, UnitCount)]

    def refresh_all_tier_styling(self) -> None:
        """Refresh tier-specific styling for all unit icons."""
        for item in self.unit_list_items:
            if hasattr(item, 'refresh_tier_styling'):
                item.refresh_tier_styling()

    def _resize_for_current_tab(self) -> None:
        """Resize the panel based on the current tab's content."""
        current_tab_name = self.get_tab(self.current_container_index)["text"]
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding - 220
        
        needs_scrollbar, content_height = self._calculate_panel_dimensions(panel_width, current_tab_name)
        
        # Calculate new panel position and size
        new_rect = pygame.Rect(
            (side_padding, pygame.display.Info().current_h - content_height - 10 - 30),
            (panel_width, content_height + 30)
        )
        
        # Only resize if dimensions actually changed
        if self.rect != new_rect:
            self.set_relative_position(new_rect.topleft)
            self.set_dimensions(new_rect.size)
            
            # Update container sizes for all tabs
            container_rect = pygame.Rect(
                (10, 10),
                (panel_width - 20, content_height - 20)
            )
            
            for container in self.containers.values():
                container.set_relative_position(container_rect.topleft)
                container.set_dimensions(container_rect.size)

    def switch_current_container(self, container_index: int) -> None:
        """Override to handle dynamic resizing when switching tabs."""
        super().switch_current_container(container_index)
        self._resize_for_current_tab()

    def cycle_to_next_faction(self) -> None:
        """Cycle to the next faction tab."""
        # Total tabs = 1 ("ALL") + number of faction tabs + 1 ("ITEMS") + 1 ("SPELLS")
        total_tabs = 1 + len(self.available_factions) + 1 + 1
        if total_tabs == 0:
            return
        
        # Since tabs are added in order: "ALL" (index 0), then factions (indices 1, 2, 3, ...), then "ITEMS", then "SPELLS" (last)
        next_tab_index = (self.current_container_index + 1) % total_tabs
        
        # Switch the container (this will automatically trigger resizing)
        self.switch_current_container(next_tab_index)
        
        # Update button selection states (needed for theme updates)
        for i, tab in enumerate(self.tabs):
            tab_button = tab["button"]
            if i == next_tab_index:
                tab_button.select()
            elif tab_button.is_selected:
                tab_button.unselect()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for the barracks."""
        # Handle Tab key to cycle through faction tabs
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.cycle_to_next_faction()
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.5
            ))
            return True

        if super().process_event(event):
            return True

        current_tab = self.get_tab(self.current_container_index)
        if current_tab is None:
            return False
            
        tab_text = current_tab["text"]
        
        # Handle events for the current tab
        if tab_text in self.entity_items:
            for item in self.entity_items[tab_text]:
                if item.handle_event(event):
                    return True
                
        return False

    def add_item(self, item_type: ItemType) -> None:
        """Add an item of the specified type to the barracks."""
        # Check if this is the first item acquired (need to show items tab)
        had_no_items = not self._has_acquired_items() and not self.sandbox_mode
        
        self._items[item_type] += 1
        
        # Check if item needs to be added to ALL tab (was count 0 before)
        was_zero = self._items[item_type] == 1 and not self.sandbox_mode
        
        if had_no_items:
            # Need to completely rebuild to add items tab
            self._full_rebuild()
        elif was_zero:
            # Need to rebuild to add item to ALL tab
            self._rebuild()
        else:
            # Just update existing counts
            self._update_entity_counts()

    def remove_item(self, item_type: ItemType) -> None:
        """Remove an item of the specified type from the barracks."""
        assert self._items[item_type] > 0
        self._items[item_type] -= 1
        
        # Check if item needs to be removed from ALL tab (count became 0)
        became_zero = self._items[item_type] == 0 and not self.sandbox_mode
        
        if became_zero:
            # Need to rebuild to remove item from ALL tab
            self._rebuild()
        else:
            # Just update existing counts
            self._update_entity_counts()

    def get_item_count(self, item_type: ItemType) -> int:
        """Get the count of a specific item type."""
        return self._items.get(item_type, 0)
    
    def has_item_available(self, item_type: ItemType) -> bool:
        """Check if an item type is available (count > 0)."""
        return self.get_item_count(item_type) > 0
    
    def add_spell(self, spell_type: SpellType) -> None:
        """Add a spell of the specified type to the barracks."""
        # Check if this is the first spell acquired (need to show spells tab)
        had_no_spells = not self._has_acquired_spells() and not self.sandbox_mode
        
        self._spells[spell_type] += 1
        
        # Check if spell needs to be added to ALL tab (was count 0 before)
        was_zero = self._spells[spell_type] == 1 and not self.sandbox_mode
        
        if had_no_spells:
            # Need to completely rebuild to add spells tab
            self._full_rebuild()
        elif was_zero:
            # Need to rebuild to add spell to ALL tab
            self._rebuild()
        else:
            # Just update existing counts
            self._update_entity_counts()

    def remove_spell(self, spell_type: SpellType) -> None:
        """Remove a spell of the specified type from the barracks."""
        assert self._spells[spell_type] > 0
        self._spells[spell_type] -= 1
        
        # Check if spell needs to be removed from ALL tab (count became 0)
        became_zero = self._spells[spell_type] == 0 and not self.sandbox_mode
        
        if became_zero:
            # Need to rebuild to remove spell from ALL tab
            self._rebuild()
        else:
            # Just update existing counts
            self._update_entity_counts()

    def get_spell_count(self, spell_type: SpellType) -> int:
        """Get the count of a specific spell type."""
        return self._spells.get(spell_type, 0)
    
    def has_spell_available(self, spell_type: SpellType) -> bool:
        """Check if a spell type is available (count > 0)."""
        return self.get_spell_count(spell_type) > 0
    
    def get_unit_count(self, unit_type: UnitType) -> int:
        """Get the count of a specific unit type."""
        return self._units.get(unit_type, 0)
    
    def has_unit_available(self, unit_type: UnitType) -> bool:
        """Check if a unit type is available (count > 0)."""
        return self.get_unit_count(unit_type) > 0
    
    def handle_button_press(self, ui_element) -> Optional[Union[UnitType, ItemType, SpellType]]:
        """
        Handle button press events and return the UnitType, ItemType, or SpellType if handled.
        Returns None if not handled.
        """
        # Check all entity items across all tabs
        for items in self.entity_items.values():
            for item in items:
                if ui_element == item.button:
                    if isinstance(item, UnitCount):
                        return item.unit_type
                    elif isinstance(item, ItemCount):
                        return item.item_type
                    elif isinstance(item, SpellCount):
                        return item.spell_type
        
        return None
    
    def get_current_tab_items(self) -> List[Union[UnitCount, ItemCount, SpellCount]]:
        """Get the items currently visible in the active tab."""
        current_tab = self.get_tab(self.current_container_index)
        if current_tab is None:
            return []
        
        tab_text = current_tab["text"]
        return self.entity_items.get(tab_text, [])
    
    def get_item_at_index(self, index: int) -> Optional[Union[UnitType, ItemType, SpellType]]:
        """
        Get the item at the specified index in the current tab.
        Returns the UnitType, ItemType, or SpellType directly, or None if index is out of bounds or item is not interactive.
        """
        current_tab_items = self.get_current_tab_items()
        
        if index < 0 or index >= len(current_tab_items):
            return None
        
        item = current_tab_items[index]
        
        # Only return interactive items (items that are available)
        if not item.interactive:
            return None
        
        # Return the appropriate type directly
        if hasattr(item, 'unit_type'):  # UnitCount
            return item.unit_type
        elif hasattr(item, 'item_type'):  # ItemCount
            return item.item_type
        elif hasattr(item, 'spell_type'):  # SpellCount
            return item.spell_type
        
        return None