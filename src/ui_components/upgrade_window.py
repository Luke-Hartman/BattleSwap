import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UIButton, UILabel, UITextBox, UIScrollableContainer
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

from components.unit_type import UnitType
from ui_components.game_data import UNIT_DATA
from upgrade_manager import upgrade_manager


class UpgradeWindow:
    """A window that displays available upgrades for a unit with descriptions."""
    
    def __init__(self, 
                 manager: pygame_gui.UIManager, 
                 unit_type: UnitType):
        """
        Initialize the upgrade window.
        
        Args:
            manager: The pygame_gui manager
            unit_type: The unit type to show upgrades for
        """
        self.manager = manager
        self.unit_type = unit_type
        self.owned_upgrades = set(upgrade_manager.get_owned_upgrades(unit_type))
        self.upgrade_points = upgrade_manager.get_upgrade_points()
        
        # Load upgrade data
        self.upgrade_data = self._load_upgrade_data()
        
        # Create the main window
        self.window = UIWindow(
            rect=pygame.Rect(100, 100, 600, 500),
            manager=manager,
            window_display_title=f"{self._get_unit_name()} Upgrades",
            element_id="upgrade_window"
        )
        
        # Create UI elements
        self._create_ui()
        
    def _load_upgrade_data(self) -> Dict[str, Any]:
        """Load upgrade data from JSON file."""
        try:
            data_path = Path("data/upgrade_data.json")
            with open(data_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: upgrade_data.json not found. Using empty upgrade data.")
            return {}
    
    def _get_unit_name(self) -> str:
        """Get the display name for the unit."""
        if self.unit_type in UNIT_DATA:
            return UNIT_DATA[self.unit_type]["name"]
        return self.unit_type.name.replace("_", " ").title()
    
    def _create_ui(self):
        """Create all UI elements for the upgrade window."""
        # Create header with unit name and upgrade points
        self.header_label = UILabel(
            relative_rect=pygame.Rect(10, 10, 580, 30),
            text=f"{self._get_unit_name()} Upgrades | Points: {self.upgrade_points}",
            manager=self.manager,
            container=self.window,
            object_id="upgrade_header"
        )
        
        # Create scrollable container for upgrades
        self.scrollable_container = UIScrollableContainer(
            relative_rect=pygame.Rect(10, 50, 580, 400),
            manager=self.manager,
            container=self.window,
            allow_scroll_x=False,
            allow_scroll_y=True
        )
        
        # Create upgrade buttons and descriptions
        self._create_upgrade_elements()
        
        # Create close button
        self.close_button = UIButton(
            relative_rect=pygame.Rect(500, 460, 90, 30),
            text="Close",
            manager=self.manager,
            container=self.window,
            object_id="upgrade_close_button"
        )
    
    def _create_upgrade_elements(self):
        """Create UI elements for each upgrade."""
        self.upgrade_buttons = {}
        self.upgrade_labels = {}
        
        unit_key = self.unit_type.name
        if unit_key not in self.upgrade_data:
            # No upgrades available for this unit
            no_upgrades_label = UILabel(
                relative_rect=pygame.Rect(10, 10, 540, 30),
                text="No upgrades available for this unit.",
                manager=self.manager,
                container=self.scrollable_container,
                object_id="no_upgrades_label"
            )
            return
        
        upgrades = self.upgrade_data[unit_key]["upgrades"]
        y_offset = 10
        
        for i, upgrade in enumerate(upgrades):
            upgrade_id = upgrade["id"]
            is_owned = upgrade_id in self.owned_upgrades
            can_afford = self.upgrade_points >= upgrade["cost"]
            prerequisites_met = self._check_prerequisites(upgrade["prerequisites"])
            
            # Determine button state
            if is_owned:
                button_text = f"✓ {upgrade['name']}"
                button_enabled = False
                button_color = "#4CAF50"  # Green for owned
            elif not prerequisites_met:
                button_text = f"🔒 {upgrade['name']}"
                button_enabled = False
                button_color = "#9E9E9E"  # Gray for locked
            elif not can_afford:
                button_text = f"💰 {upgrade['name']}"
                button_enabled = False
                button_color = "#F44336"  # Red for can't afford
            else:
                button_text = f"⬆️ {upgrade['name']}"
                button_enabled = True
                button_color = "#2196F3"  # Blue for available
            
            # Create upgrade button
            button = UIButton(
                relative_rect=pygame.Rect(10, y_offset, 300, 40),
                text=button_text,
                manager=self.manager,
                container=self.scrollable_container,
                object_id=f"upgrade_button_{upgrade_id}"
            )
            
            if not button_enabled:
                button.disable()
            
            # Create cost label
            cost_label = UILabel(
                relative_rect=pygame.Rect(320, y_offset, 80, 40),
                text=f"Cost: {upgrade['cost']}",
                manager=self.manager,
                container=self.scrollable_container,
                object_id=f"upgrade_cost_{upgrade_id}"
            )
            
            # Create description box
            description_text = upgrade["description"]
            
            # Add prerequisite information if any
            if upgrade["prerequisites"]:
                prereq_names = []
                for prereq_id in upgrade["prerequisites"]:
                    # Find the prerequisite upgrade name
                    prereq_upgrade = next((u for u in upgrades if u["id"] == prereq_id), None)
                    if prereq_upgrade:
                        prereq_names.append(prereq_upgrade["name"])
                
                if prereq_names:
                    description_text += f"\n\nRequires: {', '.join(prereq_names)}"
            
            description_box = UITextBox(
                relative_rect=pygame.Rect(10, y_offset + 45, 540, 60),
                html_text=description_text,
                manager=self.manager,
                container=self.scrollable_container,
                object_id=f"upgrade_description_{upgrade_id}"
            )
            
            # Store references
            self.upgrade_buttons[upgrade_id] = button
            self.upgrade_labels[upgrade_id] = (cost_label, description_box)
            
            y_offset += 115  # Space between upgrades
        
        # Set the scrollable area size
        self.scrollable_container.set_scrollable_area_dimensions((560, max(y_offset, 400)))
    
    def _check_prerequisites(self, prerequisites: List[str]) -> bool:
        """Check if all prerequisites are met."""
        for prereq_id in prerequisites:
            if prereq_id not in self.owned_upgrades:
                return False
        return True
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle events for the upgrade window.
        
        Args:
            event: The pygame event
            
        Returns:
            True if the event was handled, False otherwise
        """
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.close_button:
                    self.close()
                    return True
                
                # Check if it's an upgrade button
                for upgrade_id, button in self.upgrade_buttons.items():
                    if event.ui_element == button:
                        self._purchase_upgrade(upgrade_id)
                        return True
                        
            elif event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == self.window:
                    self.close()
                    return True
        
        return False
    
    def _purchase_upgrade(self, upgrade_id: str):
        """Purchase an upgrade."""
        success = upgrade_manager.purchase_upgrade(self.unit_type, upgrade_id)
        if success:
            # Refresh the UI to show the new state
            self.upgrade_points = upgrade_manager.get_upgrade_points()
            self.owned_upgrades = set(upgrade_manager.get_owned_upgrades(self.unit_type))
            
            # Update header
            self.header_label.set_text(f"{self._get_unit_name()} Upgrades | Points: {self.upgrade_points}")
            
            # Recreate upgrade elements to update button states
            # Clear existing elements first
            for button in self.upgrade_buttons.values():
                button.kill()
            for cost_label, desc_box in self.upgrade_labels.values():
                cost_label.kill()
                desc_box.kill()
            
            self.upgrade_buttons.clear()
            self.upgrade_labels.clear()
            
            # Recreate the upgrade elements
            self._create_upgrade_elements()
        else:
            print(f"Failed to purchase upgrade: {upgrade_id}")
    
    def close(self):
        """Close the upgrade window."""
        self.window.kill()
    
    def update(self, time_delta: float):
        """Update the upgrade window."""
        pass  # pygame_gui handles updates automatically
    
    def is_alive(self) -> bool:
        """Check if the window is still alive."""
        return self.window.alive()