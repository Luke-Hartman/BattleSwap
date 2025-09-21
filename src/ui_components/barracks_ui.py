"""Provides the BarracksUI component for managing available units."""
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
from selected_unit_manager import selected_unit_manager
from progress_manager import progress_manager
from point_values import unit_values, item_values
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from keyboard_shortcuts import format_button_text
from ui_components.unit_count import UnitCount
from ui_components.item_count import ItemCount




class BarracksUI(UITabContainer):
    """UI component for managing available units in the barracks."""

    def __init__(
            self,
            manager: pygame_gui.UIManager,
            starting_units: Dict[UnitType, int],
            starting_items: Dict[ItemType, int],
            interactive: bool,
            sandbox_mode: bool,
            current_battle: Optional[battles.Battle] = None,
    ):
        self.manager = manager
        self._units = starting_units.copy()
        self._items = starting_items.copy()
        self.interactive = interactive
        self.sandbox_mode = sandbox_mode
        self.current_battle = current_battle
        self.selected_unit_type: Optional[UnitType] = None
        self.selected_item_type: Optional[ItemType] = None
        
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
        
        self.available_factions = {
            Faction.faction_of(unit_type)
            for unit_type in encountered_units
        }
        
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding - 220  # Reduced width to make room for grades panel
        padding = 10
        
        needs_scrollbar, content_height = self._calculate_panel_dimensions(panel_width, "ALL")
        
        super().__init__(
            relative_rect=pygame.Rect(
                (side_padding, pygame.display.Info().current_h - content_height - 10 - 30),
                (panel_width, content_height + 30)
            ),
            manager=manager,
        )

        all_tab_index = self.add_tab("ALL", "all_tab")
        self.all_tab_index = all_tab_index
        
        self.faction_to_tab_index: Dict[Faction, int] = {}
        for faction in sorted(self.available_factions, key=lambda f: f.value):
            tab_index = self.add_tab(faction.name, "faction_tab")
            self.faction_to_tab_index[faction] = tab_index
        
        # Add items tab at the end
        items_tab_index = self.add_tab("ITEMS", "items_tab")
        self.items_tab_index = items_tab_index
        
        self.unit_containers: Dict[str, UIScrollingContainer] = {}
        self.unit_list_items_by_faction: Dict[str, List[UnitCount]] = {
            "ALL": []
        }
        
        # Item containers and lists
        self.item_containers: Dict[str, UIScrollingContainer] = {}
        self.item_list_items: List[ItemCount] = []

        for faction in self.available_factions:
            self.unit_list_items_by_faction[faction.name] = []
        
        # Create "ALL" tab container
        all_tab_panel = self.get_tab_container(all_tab_index)
        container_rect = pygame.Rect(
            (padding, padding),
            (panel_width - 2 * padding, content_height - 2 * padding)
        )
        all_container = UIScrollingContainer(
            relative_rect=container_rect,
            manager=self.manager,
            container=all_tab_panel,
            allow_scroll_y=False,
        )
        self.unit_containers["ALL"] = all_container
        
        # Create faction tab containers
        for faction in self.available_factions:
            tab_index = self.faction_to_tab_index[faction]
            tab_panel = self.get_tab_container(tab_index)
            container_rect = pygame.Rect(
                (padding, padding),
                (panel_width - 2 * padding, content_height - 2 * padding)
            )
            container = UIScrollingContainer(
                relative_rect=container_rect,
                manager=self.manager,
                container=tab_panel,
                allow_scroll_y=False,
            )
            self.unit_containers[faction.name] = container
        
        # Create items tab container
        items_tab_panel = self.get_tab_container(items_tab_index)
        items_container_rect = pygame.Rect(
            (padding, padding),
            (panel_width - 2 * padding, content_height - 2 * padding)
        )
        items_container = UIScrollingContainer(
            relative_rect=items_container_rect,
            manager=self.manager,
            container=items_tab_panel,
            allow_scroll_y=False,
        )
        self.item_containers["ITEMS"] = items_container
        
        self._populate_units(padding, needs_scrollbar)
        self._populate_items(padding, needs_scrollbar)

        # Set "ALL" tab as default
        self.switch_current_container(all_tab_index)

    def _calculate_panel_dimensions(self, panel_width: int, tab_name: str = "ALL") -> tuple[bool, int]:
        padding = 10
        
        if tab_name == "ALL":
            # Calculate units and items for "ALL" tab - only those with count > 0
            units_count = len([unit_type for unit_type, count in self._units.items() 
                              if count > 0 or self.sandbox_mode])
            if self.sandbox_mode:
                items_count = len(ItemType)
            else:
                available_items = progress_manager.available_items(self.current_battle)
                items_count = len([item_type for item_type, count in available_items.items() 
                                 if count > 0])
            total_count = units_count + items_count
        elif tab_name == "ITEMS":
            # Calculate items for "ITEMS" tab
            if self.sandbox_mode:
                items_count = len(ItemType)
            else:
                available_items = progress_manager.available_items(self.current_battle)
                items_count = len([item_type for item_type, count in available_items.items() 
                                 if count > 0])
        else:
            # Calculate units for specific faction tab
            faction = next((f for f in self.available_factions if f.name == tab_name), None)
            if faction:
                units_count = len(Faction.units(faction))
            else:
                units_count = 0
        
        if tab_name == "ITEMS":
            total_width = items_count * (ItemCount.size + padding // 2) - padding // 2 if items_count > 0 else 0
            needs_scrollbar = total_width > panel_width - 2 * padding
            panel_height = ItemCount.size + 45 if needs_scrollbar else ItemCount.size + 20
        elif tab_name == "ALL":
            # Use UnitCount.size for both units and items in "ALL" tab (they're the same size)
            total_width = total_count * (UnitCount.size + padding // 2) - padding // 2 if total_count > 0 else 0
            needs_scrollbar = total_width > panel_width - 2 * padding
            panel_height = UnitCount.size + 45 if needs_scrollbar else UnitCount.size + 20
        else:
            total_width = units_count * (UnitCount.size + padding // 2) - padding // 2 if units_count > 0 else 0
            needs_scrollbar = total_width > panel_width - 2 * padding
            panel_height = UnitCount.size + 45 if needs_scrollbar else UnitCount.size + 20

        return needs_scrollbar, panel_height

    def _populate_units(self, padding: int, needs_scrollbar: bool) -> None:
        # Populate "ALL" tab first - units and items with count > 0
        all_container = self.unit_containers["ALL"]
        container_height = all_container.rect.height
        y_offset = (container_height - UnitCount.size) // 2 if not needs_scrollbar else 0
        
        x_position = 0
        # Get all units with count > 0, sorted by type
        available_units = sorted(
            [(unit_type, count) for unit_type, count in self._units.items() 
             if count > 0 or self.sandbox_mode],
            key=lambda x: x[0].value
        )
        
        for unit_index, (unit_type, count) in enumerate(available_units):
            item = UnitCount(
                x_pos=x_position,
                y_pos=y_offset,
                unit_type=unit_type,
                count=count,
                interactive=self.interactive and count > 0,
                manager=self.manager,
                container=all_container,
                infinite=self.sandbox_mode
            )
            
            # Add keyboard shortcut tooltip for units 0-9 (keys 1-9,0)
            if unit_index < 10:
                shortcut_key = str(unit_index + 1 % 10)
                unit_name = unit_type.value.replace('_', ' ').title()
                tooltip_text = format_button_text(unit_name, shortcut_key)
                item.button.tool_tip_text = tooltip_text
                item.button.tool_tip_delay = 0
            
            self.unit_list_items_by_faction["ALL"].append(item)
            x_position += item.size + padding // 2
        
        # Add items to the "ALL" tab after units
        # Get available items
        if self.sandbox_mode:
            available_items = {item_type: float('inf') for item_type in ItemType}
        else:
            available_items = progress_manager.available_items(self.current_battle)
        
        for item_type in ItemType:
            count = available_items.get(item_type, 0)
            if count > 0 or self.sandbox_mode:
                item_count = ItemCount(
                    x_pos=x_position,
                    y_pos=y_offset,
                    item_type=item_type,
                    count=count,
                    interactive=self.interactive and count > 0,
                    manager=self.manager,
                    container=all_container
                )
                
                # Add to the same list as units for the "ALL" tab
                self.unit_list_items_by_faction["ALL"].append(item_count)
                x_position += item_count.size + padding // 2

        # Populate faction tabs - show all units for that faction (including count 0)
        for faction in self.available_factions:
            container = self.unit_containers[faction.name]
            container_height = container.rect.height
            y_offset = (container_height - UnitCount.size) // 2 if not needs_scrollbar else 0
            
            x_position = 0
            faction_units = sorted(
                [(unit_type, count) for unit_type, count in self._units.items() 
                 if Faction.faction_of(unit_type) == faction],
                key=lambda x: x[0].value
            )
            
            for unit_index, (unit_type, count) in enumerate(faction_units):
                item = UnitCount(
                    x_pos=x_position,
                    y_pos=y_offset,
                    unit_type=unit_type,
                    count=count,
                    interactive=self.interactive and count > 0,
                    manager=self.manager,
                    container=container,
                    infinite=self.sandbox_mode
                )
                
                # Add keyboard shortcut tooltip for units 0-9 (keys 1-9,0)
                if unit_index < 10:
                    shortcut_key = str(unit_index + 1 % 10)
                    unit_name = unit_type.value.replace('_', ' ').title()
                    tooltip_text = format_button_text(unit_name, shortcut_key)
                    item.button.tool_tip_text = tooltip_text
                    item.button.tool_tip_delay = 0
                
                self.unit_list_items_by_faction[faction.name].append(item)
                x_position += item.size + padding // 2

    def _rebuild(self) -> None:
        current_units = {unit_type: count for unit_type, count in self._units.items()}
        
        if not hasattr(self, '_previous_dimensions'):
            self._previous_dimensions = None
            
        # Get the current tab name
        current_tab_name = self.get_tab(self.current_container_index)["text"]
        needs_scrollbar, content_height = self._calculate_panel_dimensions(self.rect.width, current_tab_name)
        current_dimensions = (self.rect.width, content_height)
        
        if self._previous_dimensions != current_dimensions:
            # Kill "ALL" tab containers and items
            self.unit_containers["ALL"].kill()
            for item in self.unit_list_items_by_faction["ALL"]:
                item.kill()
            self.unit_list_items_by_faction["ALL"] = []
            
            # Kill faction tab containers and items
            for faction in self.available_factions:
                self.unit_containers[faction.name].kill()
                for item in self.unit_list_items_by_faction[faction.name]:
                    item.kill()
                self.unit_list_items_by_faction[faction.name] = []
            
            # Recreate "ALL" tab container
            container_rect = pygame.Rect(
                (10, 10),
                (self.rect.width - 20, content_height - 20)
            )
            all_container = UIScrollingContainer(
                relative_rect=container_rect,
                manager=self.manager,
                container=self.get_tab_container(self.all_tab_index),
                allow_scroll_y=False
            )
            self.unit_containers["ALL"] = all_container
            
            # Recreate faction tab containers
            for faction in self.available_factions:
                tab_index = self.faction_to_tab_index[faction]
                container_rect = pygame.Rect(
                    (10, 10),
                    (self.rect.width - 20, content_height - 20)
                )
                container = UIScrollingContainer(
                    relative_rect=container_rect,
                    manager=self.manager,
                    container=self.get_tab_container(tab_index),
                    allow_scroll_y=False
                )
                self.unit_containers[faction.name] = container
            
            self._populate_units(10, needs_scrollbar)
            self._previous_dimensions = current_dimensions
        else:
            # Update "ALL" tab - need to rebuild if unit availability changed
            current_available_units = set(
                unit_type for unit_type, count in current_units.items() 
                if count > 0 or self.sandbox_mode
            )
            existing_all_units = set(item.unit_type for item in self.unit_list_items_by_faction["ALL"] if isinstance(item, UnitCount))
            
            if current_available_units != existing_all_units:
                # Unit availability changed, need full rebuild
                self._previous_dimensions = None  # Force rebuild
                self._rebuild()
                return
            else:
                # Just update counts for "ALL" tab
                for item in self.unit_list_items_by_faction["ALL"]:
                    if isinstance(item, UnitCount):
                        unit_type = item.unit_type
                        count = current_units[unit_type]
                        item.update_count(count)
                        item.set_interactive(self.interactive and count > 0)
            
            # Update faction tabs
            for faction in self.available_factions:
                faction_units = {
                    unit_type: count for unit_type, count in current_units.items()
                    if Faction.faction_of(unit_type) == faction
                }
                
                for item in self.unit_list_items_by_faction[faction.name]:
                    if isinstance(item, UnitCount):
                        unit_type = item.unit_type
                        if unit_type in faction_units:
                            count = faction_units[unit_type]
                            item.update_count(count)
                            item.set_interactive(self.interactive and count > 0)


    def add_unit(self, unit_type: UnitType) -> None:
        """Add a unit of the specified type to the barracks."""
        self._units[unit_type] += 1
        
        # Update "ALL" tab
        found_in_all = False
        for item in self.unit_list_items_by_faction["ALL"]:
            if isinstance(item, UnitCount) and item.unit_type == unit_type:
                item.update_count(self._units[unit_type])
                item.set_interactive(self.interactive and self._units[unit_type] > 0)
                found_in_all = True
                break
        
        # Update faction tab
        faction = Faction.faction_of(unit_type)
        found_in_faction = False
        for item in self.unit_list_items_by_faction[faction.name]:
            if isinstance(item, UnitCount) and item.unit_type == unit_type:
                item.update_count(self._units[unit_type])
                item.set_interactive(self.interactive and self._units[unit_type] > 0)
                found_in_faction = True
                break
        
        # If unit wasn't found in "ALL" tab (was count 0 before), rebuild to add it
        if not found_in_all or not found_in_faction:
            self._rebuild()

    def remove_unit(self, unit_type: UnitType) -> None:
        """Remove a unit of the specified type from the barracks."""
        assert self._units[unit_type] > 0
        self._units[unit_type] -= 1
        
        # If count becomes 0, need to rebuild to remove from "ALL" tab
        if self._units[unit_type] == 0 and not self.sandbox_mode:
            self._rebuild()
            return
        
        # Update "ALL" tab
        for item in self.unit_list_items_by_faction["ALL"]:
            if isinstance(item, UnitCount) and item.unit_type == unit_type:
                item.update_count(self._units[unit_type])
                item.set_interactive(self.interactive and self._units[unit_type] > 0)
                break
        
        # Update faction tab
        faction = Faction.faction_of(unit_type)
        for item in self.unit_list_items_by_faction[faction.name]:
            if isinstance(item, UnitCount) and item.unit_type == unit_type:
                item.update_count(self._units[unit_type])
                item.set_interactive(self.interactive and self._units[unit_type] > 0)
                break

    def select_unit_type(self, unit_type: Optional[UnitType]) -> None:
        for faction_items in self.unit_list_items_by_faction.values():
            for item in faction_items:
                if isinstance(item, UnitCount) and item.unit_type == unit_type:
                    item.button.select()
                elif item.button.is_selected:
                    item.button.unselect()

    @property
    def units(self) -> Dict[UnitType, int]:
        return self._units.copy()

    @property
    def unit_list_items(self) -> List[UnitCount]:
        return [item for items in self.unit_list_items_by_faction.values() for item in items if isinstance(item, UnitCount)]

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
            
            for container in self.unit_containers.values():
                container.set_relative_position(container_rect.topleft)
                container.set_dimensions(container_rect.size)
            
            # Update item container sizes
            for container in self.item_containers.values():
                container.set_relative_position(container_rect.topleft)
                container.set_dimensions(container_rect.size)

    def switch_current_container(self, container_index: int) -> None:
        """Override to handle dynamic resizing when switching tabs."""
        super().switch_current_container(container_index)
        self._resize_for_current_tab()

    def cycle_to_next_faction(self) -> None:
        """Cycle to the next faction tab."""
        # Total tabs = 1 ("ALL") + number of faction tabs + 1 ("ITEMS")
        total_tabs = 1 + len(self.available_factions) + 1
        if total_tabs == 0:
            return
        
        # Since tabs are added in order: "ALL" (index 0), then factions (indices 1, 2, 3, ...), then "ITEMS" (last)
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
        if tab_text == "ALL":
            # Handle events for "ALL" tab
            for item in self.unit_list_items_by_faction["ALL"]:
                if item.handle_event(event):
                    return True
        elif tab_text == "ITEMS":
            # Handle events for items tab
            for item in self.item_list_items:
                if item.handle_event(event):
                    return True
        else:
            # Handle events for faction tabs
            tab_id = tab_text.lower() + "_tab"
            active_faction = next(f for f in Faction if f.name.lower() + '_tab' == tab_id)
                    
            for item in self.unit_list_items_by_faction[active_faction.name]:
                if item.handle_event(event):
                    return True
                
        return False

    def _populate_items(self, padding: int, needs_scrollbar: bool) -> None:
        """Populate the items tab with available items."""
        container = self.item_containers["ITEMS"]
        container_height = container.rect.height
        y_offset = (container_height - ItemCount.size) // 2 if not needs_scrollbar else 0
        
        # Clear existing items
        for item in self.item_list_items:
            item.kill()
        self.item_list_items.clear()
        
        # Get available items
        if self.sandbox_mode:
            available_items = {item_type: float('inf') for item_type in ItemType}
        else:
            available_items = progress_manager.available_items(self.current_battle)
        
        # Create item buttons
        x_position = 0
        
        for item_type in ItemType:
            count = available_items.get(item_type, 0)
            if count > 0 or self.sandbox_mode:
                item_count = ItemCount(
                    x_pos=x_position,
                    y_pos=y_offset,
                    item_type=item_type,
                    count=count,
                    interactive=self.interactive and count > 0,
                    manager=self.manager,
                    container=container
                )
                self.item_list_items.append(item_count)
                x_position += ItemCount.size + padding // 2

    def add_item(self, item_type: ItemType) -> None:
        """Add an item of the specified type to the barracks."""
        self._items[item_type] += 1
        
        # Update "ALL" tab
        found_in_all = False
        for item in self.unit_list_items_by_faction["ALL"]:
            if isinstance(item, ItemCount) and item.item_type == item_type:
                item.update_count(self._items[item_type])
                item.set_interactive(self.interactive and self._items[item_type] > 0)
                found_in_all = True
                break
        
        # Update ITEMS tab
        found_in_items = False
        for item in self.item_list_items:
            if item.item_type == item_type:
                item.update_count(self._items[item_type])
                item.set_interactive(self.interactive and self._items[item_type] > 0)
                found_in_items = True
                break
        
        # If item wasn't found in tabs (was count 0 before), rebuild to add it
        if not found_in_all or not found_in_items:
            self._rebuild()

    def remove_item(self, item_type: ItemType) -> None:
        """Remove an item of the specified type from the barracks."""
        assert self._items[item_type] > 0
        self._items[item_type] -= 1
        
        # If count becomes 0, need to rebuild to remove from tabs
        if self._items[item_type] == 0 and not self.sandbox_mode:
            self._rebuild()
            return
        
        # Update "ALL" tab
        for item in self.unit_list_items_by_faction["ALL"]:
            if isinstance(item, ItemCount) and item.item_type == item_type:
                item.update_count(self._items[item_type])
                item.set_interactive(self.interactive and self._items[item_type] > 0)
                break
        
        # Update ITEMS tab
        for item in self.item_list_items:
            if item.item_type == item_type:
                item.update_count(self._items[item_type])
                item.set_interactive(self.interactive and self._items[item_type] > 0)
                break

    def select_item_type(self, item_type: Optional[ItemType]) -> None:
        """Select an item type for placement."""
        self.selected_item_type = item_type
        for item in self.item_list_items:
            if item.item_type == item_type:
                item.button.select()
            elif item.button.is_selected:
                item.button.unselect()

    @property
    def items(self) -> Dict[ItemType, int]:
        """Get the current item counts."""
        return self._items.copy()
    
    def get_item_count(self, item_type: ItemType) -> int:
        """Get the count of a specific item type."""
        return self._items.get(item_type, 0)
    
    def has_item_available(self, item_type: ItemType) -> bool:
        """Check if an item type is available (count > 0)."""
        return self.get_item_count(item_type) > 0
    
    def get_unit_count(self, unit_type: UnitType) -> int:
        """Get the count of a specific unit type."""
        return self.units.get(unit_type, 0)
    
    def has_unit_available(self, unit_type: UnitType) -> bool:
        """Check if a unit type is available (count > 0)."""
        return self.get_unit_count(unit_type) > 0
    
    def handle_button_press(self, ui_element) -> Optional[Union[UnitType, ItemType]]:
        """
        Handle button press events and return the UnitType or ItemType if handled.
        Returns None if not handled.
        """
        # Check unit buttons
        for unit_count in self.unit_list_items:
            if ui_element == unit_count.button:
                return unit_count.unit_type
        
        # Check item buttons
        for item_count in self.item_list_items:
            if ui_element == item_count.button:
                return item_count.item_type
        
        return None
    
    def get_current_tab_items(self) -> List[Union[UnitCount, ItemCount]]:
        """Get the items currently visible in the active tab."""
        if self.current_container_index == self.all_tab_index:
            # ALL tab includes both units and items
            all_items = []
            all_items.extend(self.unit_list_items_by_faction["ALL"])
            all_items.extend(self.item_list_items)
            return all_items
        else:
            # Check if we're on a faction tab
            for faction, tab_index in self.faction_to_tab_index.items():
                if tab_index == self.current_container_index:
                    return self.unit_list_items_by_faction[faction.name]
            return []
    
    def get_item_at_index(self, index: int) -> Optional[Union[UnitType, ItemType]]:
        """
        Get the item at the specified index in the current tab.
        Returns the UnitType or ItemType directly, or None if index is out of bounds or item is not interactive.
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
        
        return None