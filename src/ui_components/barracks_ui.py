"""Provides the BarracksUI component for managing available units."""
from typing import Dict, List, Optional
import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel, UIScrollingContainer, UIButton, UILabel, UITabContainer

import battles
from components.unit_type import UnitType
from entities.units import unit_theme_ids, unit_values, Faction
from selected_unit_manager import selected_unit_manager
from progress_manager import progress_manager


class UnitCount(UIPanel):
    """A custom UI button that displays a unit icon and its count."""
    
    size = 80
    
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
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED and event.ui_element == self.button:
            selected_unit_manager.selected_unit_type = self.unit_type
            return True
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED and event.ui_element == self.button:
            selected_unit_manager.selected_unit_type = None
            return True
        return False


class BarracksUI(UITabContainer):
    """UI component for managing available units in the barracks."""

    def __init__(
            self,
            manager: pygame_gui.UIManager,
            starting_units: Dict[UnitType, int],
            interactive: bool,
            sandbox_mode: bool,
    ):
        self.manager = manager
        self._units = starting_units.copy()
        self.interactive = interactive
        self.sandbox_mode = sandbox_mode
        self.selected_unit_type: Optional[UnitType] = None
        
        if sandbox_mode:
            self._units = {unit_type: float('inf') for unit_type in UnitType}
            encountered_units = set(UnitType)
        else:
            encountered_units = set(starting_units.keys())
            for hex_coords in progress_manager.solutions:
                battle = battles.get_battle_coords(hex_coords)
                for enemy_type, _ in battle.enemies:
                    encountered_units.add(enemy_type)

            for unit_type in encountered_units:
                if unit_type not in self._units:
                    self._units[unit_type] = 0
        
        self.available_factions = {
            Faction.faction_of(unit_type)
            for unit_type in encountered_units
        }
        
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding
        padding = 10
        
        needs_scrollbar, content_height = self._calculate_panel_dimensions()
        
        super().__init__(
            relative_rect=pygame.Rect(
                (side_padding, pygame.display.Info().current_h - content_height - 10 - 30),
                (panel_width, content_height + 30)
            ),
            manager=manager,
            object_id=ObjectID(class_id='@barracks_tabs')
        )

        self.faction_to_tab_index: Dict[Faction, int] = {}
        for faction in sorted(self.available_factions, key=lambda f: f.value):
            tab_id = faction.name.lower() + '_tab'
            tab_index = self.add_tab(faction.name, '#' + tab_id)
            self.faction_to_tab_index[faction] = tab_index
        
        self.unit_containers: Dict[Faction, UIScrollingContainer] = {}
        self.unit_list_items_by_faction: Dict[Faction, List[UnitCount]] = {
            faction: [] for faction in self.available_factions
        }
        
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
                allow_scroll_y=False
            )
            self.unit_containers[faction] = container
        
        self._populate_units(padding, needs_scrollbar)

    def _calculate_panel_dimensions(self) -> tuple[bool, int]:
        padding = 10
        side_padding = 75
        panel_width = pygame.display.Info().current_w - 2 * side_padding
        
        max_units = max(
            len(Faction.units(faction))
            for faction in self.available_factions
        ) if self.available_factions else 0
        
        total_width = max_units * (UnitCount.size + padding // 2) - padding // 2 if max_units > 0 else 0
        needs_scrollbar = total_width > panel_width - 2 * padding
        panel_height = UnitCount.size + 45 if needs_scrollbar else UnitCount.size + 20

        return needs_scrollbar, panel_height

    def _populate_units(self, padding: int, needs_scrollbar: bool) -> None:
        for faction in self.available_factions:
            container = self.unit_containers[faction]
            container_height = container.rect.height
            y_offset = (container_height - UnitCount.size) // 2 if not needs_scrollbar else 0
            
            x_position = 0
            faction_units = sorted(
                [(unit_type, count) for unit_type, count in self._units.items() 
                 if Faction.faction_of(unit_type) == faction],
                key=lambda x: x[0].value
            )
            
            for unit_type, count in faction_units:
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
                self.unit_list_items_by_faction[faction].append(item)
                x_position += item.size + padding // 2

    def _rebuild(self) -> None:
        for faction in self.available_factions:
            self.unit_containers[faction].kill()
            for item in self.unit_list_items_by_faction[faction]:
                item.kill()
            self.unit_list_items_by_faction[faction] = []
        
        needs_scrollbar, content_height = self._calculate_panel_dimensions()
        
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
            self.unit_containers[faction] = container
        
        self._populate_units(10, needs_scrollbar)

    def add_unit(self, unit_type: UnitType) -> None:
        self._units[unit_type] += 1
        self._rebuild()

    def remove_unit(self, unit_type: UnitType) -> None:
        assert self._units[unit_type] > 0
        self._units[unit_type] -= 1
        self._rebuild()

    def select_unit_type(self, unit_type: Optional[UnitType]) -> None:
        for faction_items in self.unit_list_items_by_faction.values():
            for item in faction_items:
                if item.unit_type == unit_type:
                    item.button.select()
                elif item.button.is_selected:
                    item.button.unselect()

    @property
    def units(self) -> Dict[UnitType, int]:
        return self._units.copy()

    @property
    def unit_list_items(self) -> List[UnitCount]:
        return [item for items in self.unit_list_items_by_faction.values() for item in items]

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().process_event(event):
            return True

        current_tab = self.get_tab(self.current_container_index)
        if current_tab is None:
            return False
            
        tab_id = current_tab["text"].lower() + "_tab"
        active_faction = next(f for f in Faction if f.name.lower() + '_tab' == tab_id)
        for item in self.unit_list_items_by_faction[active_faction]:
            if item.handle_event(event):
                return True
                
        return False