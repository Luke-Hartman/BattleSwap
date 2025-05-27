import pygame
import pygame_gui
from typing import List, Tuple
from ui_components.stat_bar import StatBar
from components.unit_type import UnitType
from entities.units import Faction
from ui_components.game_data import StatType, UNIT_DATA
from unit_values import unit_values
from pygame_gui.elements import UILabel, UIButton
from info_mode_manager import info_mode_manager
from ui_components.glossary_entry import GlossaryEntry

class UnitCard:
    """A UI component that displays a unit card with a name, description, and stats."""
    
    def __init__(self, 
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 name: str,
                 description: str,
                 unit_type: UnitType):
        """
        Initialize a UnitCard component.
        
        Args:
            manager: The UI manager for this component
            position: The (x, y) position to place the window
            name: The name of the unit
            description: The HTML description of the unit (can include links)
            unit_type: The type of unit to display the image for
        """
        self.manager = manager
        self.name = name
        self.stat_bars: List[StatBar] = []
        self.unit_type = unit_type
        
        # Create the window
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(position, (300, 420)),
            window_display_title=f"{name} - {Faction.faction_of(unit_type).name.title()}",
            manager=manager,
            resizable=False
        )
        
        # Add description
        full_description = f"{description}"
        
        # Add unit description with clickable links
        self.text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((0, 0), (300, 150)),
            html_text=full_description,
            manager=manager,
            container=self.window
        )
        
        # Store the window reference in the text box's container for link handling
        self.text.ui_container.window = self.window

        # Add bottom row with label and Tips button
        bottom_y = 350
        self.bottom_label = UILabel(
            relative_rect=pygame.Rect((10, bottom_y), (180, 30)),
            text="",
            manager=manager,
            container=self.window
        )
        self.tips_button = UIButton(
            relative_rect=pygame.Rect((300-90, bottom_y), (80, 30)),
            text="Tips",
            manager=manager,
            container=self.window
        )
    
    def add_stat(self, 
                stat_type: StatType, 
                value: int,
                tooltip_text: str):
        """
        Add a stat bar to the unit card.
        
        Args:
            stat_type: The type of stat
            value: The value (0-10) of the stat
            tooltip_text: Text to display when hovering over the stat
        """
        # Constants for positioning stats
        y_offset = 150
        bar_height = 35
        spacing = 5
        
        # Create the stat bar
        stat_bar = StatBar(
            manager=self.manager,
            rect=pygame.Rect(
                (10, y_offset + len(self.stat_bars) * (bar_height + spacing)), 
                (280, bar_height)
            ),
            container=self.window,
            stat_type=stat_type,
            value=value,
            tooltip_text=tooltip_text,
            disabled=False
        )
        
        self.stat_bars.append(stat_bar)
        return stat_bar

    def skip_stat(self, stat_type: StatType):
        """
        Add a stat bar that is grayed out because it doesn't apply to this unit.
        
        Args:
            stat_type: The type of stat
        """
        # Constants for positioning stats
        y_offset = 150
        bar_height = 35
        spacing = 5
        
        # Create the stat bar
        stat_bar = StatBar(
            manager=self.manager,
            rect=pygame.Rect(
                (10, y_offset + len(self.stat_bars) * (bar_height + spacing)), 
                (280, bar_height)
            ),
            container=self.window,
            stat_type=stat_type,
            value=0,
            tooltip_text="",
            disabled=True
        )
        
        self.stat_bars.append(stat_bar)
        return stat_bar
    
    def get_window(self):
        """Get the window element for this unit card."""
        return self.window
    
    def kill(self):
        """Remove the unit card from the UI."""
        self.window.kill()
        self.bottom_label.kill()
        self.tips_button.kill()
        
    def update(self, time_delta: float):
        """Update all stat bars."""
        for stat_bar in self.stat_bars:
            stat_bar.update(time_delta)

        if info_mode_manager.info_mode:
            self.bottom_label.set_text(f"Press {info_mode_manager.modifier_key} to close")
        else:
            self.bottom_label.set_text(f"Press {info_mode_manager.modifier_key} to keep open")

    def show_tips(self):
        """Show a glossary entry with tips for this unit at the mouse position."""
        tips = UNIT_DATA[self.unit_type].get("tips", "No tips available for this unit.")
        mouse_pos = pygame.mouse.get_pos()
        GlossaryEntry(
            manager=self.manager,
            position=mouse_pos,
            title=f"{self.name} Tips",
            content='\n'.join(f'  {tip}' for tip in tips)
        )

    def process_event(self, event):
        """Process UI events for the unit card (e.g., Tips button click). Returns True if handled."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.tips_button:
            self.show_tips()
            return True
        return False 