import pygame
import pygame_gui
from typing import List, Optional, Dict
from pygame_gui.elements import UIWindow, UIScrollingContainer, UIPanel, UIButton, UILabel, UIImage
from pygame_gui.core import ObjectID

import battles
from components.unit_type import UnitType
from components.unit_tier import UnitTier
from entities.units import Faction, unit_theme_ids
from progress_manager import progress_manager
from ui_components.game_data import get_unit_data
# from ui_components.unit_card import UnitCard  # Not needed in this file
from unit_values import unit_values

class UnitTierUpgradeUI:
    """UI component for upgrading unit tiers."""
    
    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager):
        self.screen = screen
        self.manager = manager
        self.selected_unit_type: Optional[UnitType] = None
        
        # Create main window
        window_width = 1000
        window_height = 700
        window_pos = (
            (screen.get_width() - window_width) // 2,
            (screen.get_height() - window_height) // 2
        )
        
        self.window = UIWindow(
            rect=pygame.Rect(window_pos, (window_width, window_height)),
            window_display_title="Unit Tier Upgrades",
            manager=manager,
            resizable=False
        )
        
        # Create top section for units list
        self.units_container = UIScrollingContainer(
            relative_rect=pygame.Rect((10, 10), (980, 200)),
            manager=manager,
            container=self.window
        )
        
        # Create credits display
        self.credits_label = UILabel(
            relative_rect=pygame.Rect((10, 220), (980, 30)),
            text=f"Advanced Credits: {progress_manager.advanced_credits} | Elite Credits: {progress_manager.elite_credits}",
            manager=manager,
            container=self.window,
            object_id=ObjectID(class_id="@centered_text")
        )
        
        # Create bottom section for tier cards
        self.tier_cards_container = UIPanel(
            relative_rect=pygame.Rect((10, 260), (980, 390)),
            manager=manager,
            container=self.window
        )
        
        # Create close button
        self.close_button = UIButton(
            relative_rect=pygame.Rect((900, 660), (80, 30)),
            text="Close",
            manager=manager,
            container=self.window
        )
        
        # Initialize unit buttons and tier cards
        self.unit_buttons: List[UIButton] = []
        self.tier_cards: List['UnitCardPanel'] = []
        
        self._create_unit_buttons()
        
    def _create_unit_buttons(self):
        """Create buttons for all unlocked units."""
        # Get all unlocked units
        unlocked_units = set()
        
        # Add starting units
        for unit_type in battles.starting_units.keys():
            unlocked_units.add(unit_type)
            
        # Add units from completed battles
        for hex_coords in progress_manager.solutions:
            battle = battles.get_battle_coords(hex_coords)
            for enemy_type, _ in battle.enemies:
                unlocked_units.add(enemy_type)
        
        # Sort units by faction and then by name
        sorted_units = sorted(
            unlocked_units,
            key=lambda u: (Faction.faction_of(u).value, u.value)
        )
        
        # Create buttons
        button_size = 80
        x_offset = 10
        y_offset = 10
        
        for i, unit_type in enumerate(sorted_units):
            x = x_offset + (i * (button_size + 10))
            
            # Get current tier for border color
            current_tier = progress_manager.get_unit_tier(unit_type)
            
            # Determine button style based on tier
            if current_tier == UnitTier.ADVANCED:
                object_id = ObjectID(class_id="@unit_tier_advanced", object_id=unit_theme_ids[unit_type])
            elif current_tier == UnitTier.ELITE:
                object_id = ObjectID(class_id="@unit_tier_elite", object_id=unit_theme_ids[unit_type])
            else:
                object_id = ObjectID(class_id="@unit_tier_basic", object_id=unit_theme_ids[unit_type])
            
            button = UIButton(
                relative_rect=pygame.Rect((x, y_offset), (button_size, button_size)),
                text="",
                manager=self.manager,
                container=self.units_container,
                object_id=object_id
            )
            button.unit_type = unit_type  # Store unit type for later reference
            self.unit_buttons.append(button)
        
        # Set the container size based on content
        total_width = len(sorted_units) * (button_size + 10) + 20
        self.units_container.set_scrollable_area_dimensions((total_width, 100))
    
    def _select_unit(self, unit_type: UnitType):
        """Select a unit and show its tier cards."""
        self.selected_unit_type = unit_type
        
        # Clear existing tier cards
        for card in self.tier_cards:
            card.kill()
        self.tier_cards.clear()
        
        # Create tier cards for Basic, Advanced, and Elite
        card_width = 300
        card_spacing = 20
        start_x = (980 - (3 * card_width + 2 * card_spacing)) // 2
        
        current_tier = progress_manager.get_unit_tier(unit_type)
        
        for i, tier in enumerate([UnitTier.BASIC, UnitTier.ADVANCED, UnitTier.ELITE]):
            x = start_x + i * (card_width + card_spacing)
            
            # Get unit data for this tier
            unit_data = get_unit_data(unit_type, tier)
            
            # Create panel-based unit card
            card = UnitCardPanel(
                screen=self.screen,
                manager=self.manager,
                position=(x, 10),
                name=unit_data.name,
                description=unit_data.description,
                unit_type=unit_type,
                unit_tier=tier,
                container=self.tier_cards_container,
                current_tier=current_tier
            )
            
            self.tier_cards.append(card)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events."""
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.close_button:
                    self.kill()
                    return True
                
                # Check if it's a unit button
                for button in self.unit_buttons:
                    if event.ui_element == button:
                        self._select_unit(button.unit_type)
                        return True
                
                # Check if it's an upgrade button
                for card in self.tier_cards:
                    if isinstance(card, UnitCardPanel) and hasattr(card, 'upgrade_button') and card.upgrade_button and event.ui_element == card.upgrade_button:
                        if self._upgrade_unit(card.unit_type, card.unit_tier):
                            # Refresh the display
                            self._update_credits_display()
                            self._refresh_unit_buttons()
                            if self.selected_unit_type:
                                self._select_unit(self.selected_unit_type)
                        return True
        
        return False
    
    def _upgrade_unit(self, unit_type: UnitType, target_tier: UnitTier) -> bool:
        """Attempt to upgrade a unit to the target tier."""
        current_tier = progress_manager.get_unit_tier(unit_type)
        
        if current_tier == UnitTier.BASIC and target_tier == UnitTier.ADVANCED:
            return progress_manager.upgrade_unit(unit_type)
        elif current_tier == UnitTier.ADVANCED and target_tier == UnitTier.ELITE:
            return progress_manager.upgrade_unit(unit_type)
        
        return False
    
    def _update_credits_display(self):
        """Update the credits display."""
        self.credits_label.set_text(
            f"Advanced Credits: {progress_manager.advanced_credits} | Elite Credits: {progress_manager.elite_credits}"
        )
    
    def _refresh_unit_buttons(self):
        """Refresh unit buttons to show updated tier colors."""
        for button in self.unit_buttons:
            current_tier = progress_manager.get_unit_tier(button.unit_type)
            
            # Update button style based on tier
            if current_tier == UnitTier.ADVANCED:
                object_id = ObjectID(class_id="@unit_tier_advanced", object_id=unit_theme_ids[button.unit_type])
            elif current_tier == UnitTier.ELITE:
                object_id = ObjectID(class_id="@unit_tier_elite", object_id=unit_theme_ids[button.unit_type])
            else:
                object_id = ObjectID(class_id="@unit_tier_basic", object_id=unit_theme_ids[button.unit_type])
            
            button.change_object_id(object_id)
    
    def kill(self):
        """Close the upgrade UI."""
        for card in self.tier_cards:
            card.kill()
        self.window.kill()


class UnitCardPanel:
    """A panel-based version of UnitCard for use in the tier upgrade UI."""
    
    def __init__(self, 
                 screen: pygame.Surface,
                 manager: pygame_gui.UIManager,
                 position: tuple[int, int],
                 name: str,
                 description: str,
                 unit_type: UnitType,
                 unit_tier: UnitTier,
                 container: UIPanel,
                 current_tier: UnitTier):
        
        self.screen = screen
        self.manager = manager
        self.unit_type = unit_type
        self.unit_tier = unit_tier
        self.current_tier = current_tier
        
        # Create main panel with tier-based border
        tier_class = self._get_tier_class(unit_tier)
        
        self.panel = UIPanel(
            relative_rect=pygame.Rect(position, (300, 360)),
            manager=manager,
            container=container,
            object_id=ObjectID(class_id=tier_class)
        )
        
        # Create unit card content (simplified version)
        self._create_content(name, description, unit_type, unit_tier)
        
        # Create upgrade button if applicable
        self._create_upgrade_button()
    
    def _get_tier_class(self, tier: UnitTier) -> str:
        """Get the CSS class for the tier border."""
        if tier == UnitTier.ADVANCED:
            return "@unit_card_advanced"
        elif tier == UnitTier.ELITE:
            return "@unit_card_elite"
        else:
            return "@unit_card_basic"
    
    def _create_content(self, name: str, description: str, unit_type: UnitType, unit_tier: UnitTier):
        """Create the content of the unit card panel."""
        # Title with tier
        if unit_tier != UnitTier.BASIC:
            title = f"{name} ({unit_tier.value})"
        else:
            title = name
            
        self.title_label = UILabel(
            relative_rect=pygame.Rect((10, 10), (280, 30)),
            text=title,
            manager=self.manager,
            container=self.panel,
            object_id=ObjectID(class_id="@centered_text")
        )
        
        # Point value
        point_value = unit_values.get(unit_type, 0)
        self.points_label = UILabel(
            relative_rect=pygame.Rect((10, 45), (280, 25)),
            text=f"Cost: {point_value} points",
            manager=self.manager,
            container=self.panel,
            object_id=ObjectID(class_id="@centered_text")
        )
        
        # Description
        self.description_box = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((10, 75), (280, 80)),
            html_text=description,
            manager=self.manager,
            container=self.panel
        )
        
        # Stats summary (simplified)
        unit_data = get_unit_data(unit_type, unit_tier)
        stats_text = self._create_stats_summary(unit_data)
        
        self.stats_label = UILabel(
            relative_rect=pygame.Rect((10, 160), (280, 35)),
            text=stats_text,
            manager=self.manager,
            container=self.panel,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        
        # Current tier indicator
        if unit_tier == self.current_tier:
            indicator_text = "CURRENT TIER"
            color_class = "@current_tier_text"
        elif unit_tier.value in ["Advanced", "Elite"] and self.current_tier == UnitTier.BASIC:
            indicator_text = "LOCKED"
            color_class = "@locked_tier_text"
        elif unit_tier == UnitTier.ELITE and self.current_tier == UnitTier.ADVANCED:
            indicator_text = "LOCKED"
            color_class = "@locked_tier_text"
        else:
            indicator_text = "AVAILABLE"
            color_class = "@available_tier_text"
            
        self.tier_indicator = UILabel(
            relative_rect=pygame.Rect((10, 200), (280, 25)),
            text=indicator_text,
            manager=self.manager,
            container=self.panel,
            object_id=ObjectID(class_id=color_class)
        )
    
    def _create_upgrade_button(self):
        """Create upgrade button if this tier can be upgraded to."""
        self.upgrade_button = None
        
        # Only show upgrade button for the next available tier
        if (self.current_tier == UnitTier.BASIC and self.unit_tier == UnitTier.ADVANCED and 
            progress_manager.can_upgrade_unit(self.unit_type)):
            
            self.upgrade_button = UIButton(
                relative_rect=pygame.Rect((10, 320), (280, 30)),
                text=f"Upgrade (1 Advanced Credit)",
                manager=self.manager,
                container=self.panel
            )
            
        elif (self.current_tier == UnitTier.ADVANCED and self.unit_tier == UnitTier.ELITE and 
              progress_manager.can_upgrade_unit(self.unit_type)):
            
            self.upgrade_button = UIButton(
                relative_rect=pygame.Rect((10, 320), (280, 30)),
                text=f"Upgrade (1 Elite Credit)",
                manager=self.manager,
                container=self.panel
            )
    
    def _create_stats_summary(self, unit_data):
        """Create a summary of the unit's stats."""
        stats_lines = []
        from ui_components.game_data import StatType
        
        for stat_type in StatType:
            stat_value = unit_data.stats.get(stat_type)
            if stat_value is not None:
                # Convert stat value to visual representation (stars)
                stars = "★" * int(stat_value) + "☆" * (10 - int(stat_value))
                stats_lines.append(f"{stat_type.value.title()}: {stars[:5]}")
        
        return " | ".join(stats_lines[:2])  # Show first 2 stats only
    
    def kill(self):
        """Remove the panel and all its contents."""
        self.panel.kill()