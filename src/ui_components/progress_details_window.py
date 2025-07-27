"""Progress details window UI component."""

import pygame
import pygame_gui
from typing import Set, Tuple
from collections import defaultdict

import battles
from progress_manager import progress_manager, HexLifecycleState
from components.unit_type import UnitType
from components.unit_tier import UnitTier


class ProgressDetailsWindow:
    """A modal window displaying detailed progress statistics."""
    
    def __init__(self, manager: pygame_gui.UIManager):
        """Initialize the progress details window."""
        self.manager = manager
        self.window = None
        self.close_button = None
        self._create_window()
    
    def _create_window(self) -> None:
        """Create the progress details window and its contents."""
        # Get screen dimensions
        screen_info = pygame.display.Info()
        screen_width = screen_info.current_w
        screen_height = screen_info.current_h
        
        # Window dimensions
        window_width = 600
        window_height = 450
        
        # Center the window
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2
        
        # Create the main window
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(window_x, window_y, window_width, window_height),
            manager=self.manager,
            window_display_title="Progress Details",
            resizable=False,
        )
        
        # Create close button in the top-right corner
        close_button_size = (30, 30)
        close_button_x = window_width - close_button_size[0] - 10
        close_button_y = 10
        
        self.close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(close_button_x, close_button_y, *close_button_size),
            text="X",
            manager=self.manager,
            container=self.window,
            anchors={'left': 'right',
                    'right': 'right',
                    'top': 'top',
                    'bottom': 'top'}
        )
        
        # Calculate and display progress statistics
        stats_html = self._generate_stats_html()
        
        # Create text box with statistics
        self.stats_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 10, window_width - 20, window_height - 50),
            html_text=stats_html,
            manager=self.manager,
            container=self.window,
            wrap_to_height=True,
        )
    
    def _generate_stats_html(self) -> str:
        """Generate HTML content for the progress statistics."""
        # Get all unit types from battles
        all_unit_types = set(UnitType)
        
        # Get all battles (excluding test battles)
        all_battles = [b for b in battles.get_battles() if not b.is_test]
        
        # Track encountered and unlocked units
        encountered_units = set()
        unlocked_units = set()
        
        # Track hexes
        total_hexes = len(all_battles)
        encountered_hexes = 0
        claimed_hexes = 0
        reclaimed_hexes = 0
        
        # Process each battle to gather statistics
        for battle in all_battles:
            hex_coords = battle.hex_coords
            hex_state = progress_manager.get_hex_state(hex_coords)
            
            # Count hex states
            if hex_state != HexLifecycleState.FOGGED:
                encountered_hexes += 1
                
                # Add enemy units to encountered units
                if battle.enemies:
                    for unit_type, _ in battle.enemies:
                        encountered_units.add(unit_type)
            
            if hex_state in [HexLifecycleState.CLAIMED, HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]:
                claimed_hexes += 1
                
                # Add enemy units to unlocked units (from claimed battles)
                if battle.enemies:
                    for unit_type, _ in battle.enemies:
                        unlocked_units.add(unit_type)
            
            if hex_state == HexLifecycleState.RECLAIMED:
                reclaimed_hexes += 1
        
        # Count upgraded units
        advanced_units = 0
        elite_units = 0
        
        for unit_type in all_unit_types:
            tier = progress_manager.get_unit_tier(unit_type)
            if tier == UnitTier.ADVANCED:
                advanced_units += 1
            elif tier == UnitTier.ELITE:
                elite_units += 1
        
        # Format statistics
        total_unit_types = len(all_unit_types)
        
        stats_html = f"""<font size=4><b>Campaign Progress Details</b></font><br><br>

<b>Unit Discovery:</b><br>
• Units encountered: <b>{len(encountered_units)}/{total_unit_types}</b><br>
• Units unlocked: <b>{len(unlocked_units)}/{total_unit_types}</b><br><br>

<b>Unit Upgrades:</b><br>
• Units upgraded to Advanced: <b>{advanced_units}/{total_unit_types}</b><br>
• Units upgraded to Elite: <b>{elite_units}/{total_unit_types}</b><br><br>

<b>Map Progress:</b><br>
• Hexes encountered: <b>{encountered_hexes}/{total_hexes}</b><br>
• Hexes claimed: <b>{claimed_hexes}/{total_hexes}</b><br>
• Hexes reclaimed: <b>{reclaimed_hexes}/{total_hexes}</b><br><br>

<font size=2><i>Units are encountered when you discover battles with unfogged enemies.<br>
Units are unlocked when you complete battles and gain access to those unit types.<br>
Hexes are encountered when they become unfogged and accessible.<br>
Hexes are claimed when you complete battles or corruption challenges.<br>
Hexes are reclaimed when you complete them again after corruption.</i></font>"""
        
        return stats_html
    
    def is_alive(self) -> bool:
        """Check if the window is still alive."""
        return self.window is not None and self.window.alive()
    
    def kill(self) -> None:
        """Close and destroy the window."""
        if self.window is not None:
            self.window.kill()
            self.window = None
            self.close_button = None
            self.stats_text = None
    
    def process_event(self, event: pygame.event.Event) -> bool:
        """Process UI events for this window."""
        if not self.is_alive():
            return False
            
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.close_button:
                self.kill()
                return True
                
        if event.type == pygame_gui.UI_WINDOW_CLOSE:
            if event.ui_element == self.window:
                self.kill()
                return True
        
        return False