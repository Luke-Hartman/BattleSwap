import pygame
import pygame_gui
import sys
from typing import Dict, List

from ui_components.game_data import (
    GlossaryEntryType, 
    UnitType, 
    StatType, 
    GLOSSARY_ENTRIES,
    UNIT_DATA
)
from ui_components.glossary_entry import GlossaryEntry
from ui_components.unit_card import UnitCard
from pathlib import Path
import os
from info_mode_manager import info_mode_manager

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return Path(base_path) / relative_path

class NestedTooltipDemo:
    """
    Demo application showcasing unit cards with stats and linked glossary entries.
    """
    def __init__(self):
        from entities.units import load_sprite_sheets
        pygame.init()
        
        # Set up the display
        self.WINDOW_SIZE = (1200, 800)
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption("Game Unit Cards & Glossary Demo")

        load_sprite_sheets()
        
        # Initialize the UI manager with the game's theme
        theme_path = str(get_resource_path('data/theme.json'))
        self.ui_manager = pygame_gui.UIManager(self.WINDOW_SIZE, theme_path)
        
        # Create unit showcase buttons
        self.create_unit_buttons()
        
        # Create info mode text
        self.info_mode_text = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.WINDOW_SIZE[0]//2 - 150, 50), (300, 30)),
            text='Info Mode Active - Press Command to Exit',
            manager=self.ui_manager
        )
        self.info_mode_text.visible = False
        
        # Track active UI elements
        self.active_windows = {}  # Dictionary to store windows by their ID
        self.unit_cards: List[UnitCard] = []
        self.glossary_entries: List[GlossaryEntry] = []
        
        # Hover state tracking
        self.hovered_button = None
        self.hover_card = None
        self.hover_position = None
        
        # Clock for frame rate
        self.clock = pygame.time.Clock()
    
    def create_unit_buttons(self):
        """Create buttons for each unit type arranged in a grid."""
        units = list(UNIT_DATA.keys())
        
        # Button dimensions
        button_width = 150
        button_height = 50
        
        # Grid configuration
        columns = 3  # Number of columns in the grid
        spacing_x = 20  # Horizontal spacing between buttons
        spacing_y = 20  # Vertical spacing between buttons
        
        # Calculate grid parameters
        rows = (len(units) + columns - 1) // columns  # Ceiling division to get required rows
        
        # Calculate total width and height of the grid
        total_width = columns * button_width + (columns - 1) * spacing_x
        total_height = rows * button_height + (rows - 1) * spacing_y
        
        # Calculate starting position to center the grid
        start_x = (self.WINDOW_SIZE[0] - total_width) // 2
        start_y = (self.WINDOW_SIZE[1] - total_height) // 2
        
        self.unit_buttons = {}
        
        for i, unit_type in enumerate(units):
            # Calculate row and column positions
            row = i // columns
            col = i % columns
            
            # Calculate x and y positions for this button
            x = start_x + col * (button_width + spacing_x)
            y = start_y + row * (button_height + spacing_y)
            
            unit_data = UNIT_DATA[unit_type]
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (x, y),
                    (button_width, button_height)
                ),
                text=unit_data["name"],
                manager=self.ui_manager
            )
            self.unit_buttons[button] = unit_type
    
    def create_unit_card(self, unit_type: UnitType, position = None):
        """Create a unit card for the given unit type."""
        # Clear existing cards if not in info mode and not a hover card
        if not info_mode_manager.info_mode and not self.hover_card:
            self.clear_all_windows()
        
        # Get unit data
        unit_data = UNIT_DATA[unit_type]
        
        # Set default position if none provided
        if position is None:
            # Position card on the right side of the screen, centered vertically
            card_width = 300  # Width of the unit card
            card_height = 400  # Height of the unit card
            position = (
                self.WINDOW_SIZE[0] - card_width - 20,  # 20px padding from right edge
                (self.WINDOW_SIZE[1] - card_height) // 2  # Center vertically
            )
            
        # Create the unit card
        unit_card = UnitCard(
            screen=self.screen,
            manager=self.ui_manager,
            position=position,
            name=unit_data["name"],
            description=unit_data["description"],
            unit_type=unit_type
        )
        
        # Add all stats to the card, with non-applicable ones being grayed out
        for stat_type in StatType:
            if stat_type in unit_data["stats"]:
                unit_card.add_stat(
                    stat_type=stat_type,
                    value=unit_data["stats"][stat_type],
                    tooltip_text=unit_data["tooltips"][stat_type]
                )
            else:
                unit_card.skip_stat(
                    stat_type=stat_type
                )
                
        # Track the card and its window
        self.unit_cards.append(unit_card)
        self.active_windows[unit_card.get_window()] = unit_card
        
        return unit_card
    
    def create_glossary_entry(self, entry_type_str: str, click_position: tuple[int, int]):
        """Create a glossary entry window."""
        # Find the matching entry type
        entry_type = None
        for glossary_type in GlossaryEntryType:
            if glossary_type.value == entry_type_str:
                entry_type = glossary_type
                break
                
        if entry_type is None:
            return None
            
        # Get entry data
        entry_data = GLOSSARY_ENTRIES[entry_type]
        
        # Create the entry
        glossary_entry = GlossaryEntry.from_click_position(
            manager=self.ui_manager,
            title=entry_type.value,
            content=entry_data,
            click_position=click_position
        )
        
        # Track the entry and its window
        self.glossary_entries.append(glossary_entry)
        self.active_windows[glossary_entry.get_window()] = glossary_entry
        
        return glossary_entry
    
    def clear_all_windows(self):
        """Clear all active windows."""
        # Kill all windows
        for window_obj in self.active_windows.values():
            window_obj.kill()
            
        # Clear tracking collections
        self.active_windows.clear()
        self.unit_cards.clear()
        self.glossary_entries.clear()
    
    def run(self):
        """Run the main application loop."""
        running = True
        while running:
            time_delta = self.clock.tick(60)/1000.0
            
            # Get mouse position
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for button hover (only if not in info mode)
            current_hover = None
            if not info_mode_manager.info_mode:
                for button, unit_type in self.unit_buttons.items():
                    if button.relative_rect.collidepoint(mouse_pos):
                        current_hover = (button, unit_type)
                        break
            
            # Handle hover state changes
            if current_hover != self.hovered_button:
                # Clear previous hover card if not in info mode
                if self.hover_card and not info_mode_manager.info_mode:
                    self.hover_card.kill()
                    self.hover_card = None
                
                self.hovered_button = current_hover
                
                # Create new hover card if hovering over a button
                if current_hover and not info_mode_manager.info_mode:
                    button, unit_type = current_hover
                    self.hover_card = self.create_unit_card(unit_type=unit_type)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle command key press for info mode toggle
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LMETA or event.key == pygame.K_RMETA:  # Command key
                        info_mode_manager.info_mode = not info_mode_manager.info_mode
                        self.info_mode_text.visible = info_mode_manager.info_mode  # Show/hide info mode text
                        # If entering info mode, keep current hover card
                        if info_mode_manager.info_mode and self.hover_card:
                            self.unit_cards.append(self.hover_card)
                            self.active_windows[self.hover_card.get_window()] = self.hover_card
                        # If exiting info mode, clear all cards
                        elif not info_mode_manager.info_mode:
                            self.clear_all_windows()
                            self.hover_card = None
                
                # Handle window close events
                if event.type == pygame_gui.UI_WINDOW_CLOSE:
                    if event.ui_element in self.active_windows:
                        window_obj = self.active_windows[event.ui_element]
                        
                        # Remove from appropriate collection
                        if isinstance(window_obj, UnitCard):
                            self.unit_cards.remove(window_obj)
                            if window_obj == self.hover_card:
                                self.hover_card = None
                        elif isinstance(window_obj, GlossaryEntry):
                            self.glossary_entries.remove(window_obj)
                            
                        # Remove from active windows
                        del self.active_windows[event.ui_element]
                        
                        # If no more windows are open, exit info mode
                        if not self.active_windows and info_mode_manager.info_mode:
                            info_mode_manager.info_mode = False
                            self.info_mode_text.visible = False
                
                # Handle text link clicks
                if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
                    mouse_pos = pygame.mouse.get_pos()
                    self.create_glossary_entry(
                        entry_type_str=event.link_target,
                        click_position=mouse_pos
                    )
                
                event_handled = False
                for unit_card in self.unit_cards:
                    if hasattr(unit_card, 'process_event') and unit_card.process_event(event):
                        event_handled = True
                        break
                if not event_handled:
                    self.ui_manager.process_events(event)
            
            # Update unit cards
            for unit_card in self.unit_cards:
                unit_card.update(time_delta)
            
            self.ui_manager.update(time_delta)
            
            # Use the game's background color
            self.screen.fill((13, 46, 75))  # MAP_BACKGROUND_COLOR from game_constants
            self.ui_manager.draw_ui(self.screen)
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = NestedTooltipDemo()
    app.run()
