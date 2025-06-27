"""UI component for upgrading unit tiers."""

from typing import Dict, List, Optional, Tuple
import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UIScrollingContainer, UIButton, UILabel, UIWindow
from pygame_gui.core import ObjectID

from components.unit_type import UnitType
from components.unit_tier import UnitTier
from entities.units import Faction, unit_theme_ids
from progress_manager import progress_manager
from ui_components.unit_card import UnitCard
from ui_components.game_data import UNIT_DATA
from unit_values import unit_values


class UnitUpgradeButton(UIPanel):
    """A button representing a unit that can be clicked to view its upgrade options."""
    
    size = 80
    
    def __init__(self, 
                 x_pos: int,
                 y_pos: int,
                 unit_type: UnitType,
                 manager: pygame_gui.UIManager,
                 container: Optional[pygame_gui.core.UIContainer] = None):
        self.unit_type = unit_type
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
        
        # Add tier indicator
        current_tier = progress_manager.get_unit_tier(unit_type)
        tier_text = current_tier.value[0]  # First letter (B/A/E)
        
        self.tier_label = UILabel(
            relative_rect=pygame.Rect((0, self.size - 25), (self.size, 25)),
            text=tier_text,
            manager=manager,
            container=self,
            object_id=ObjectID(class_id="@unit_tier_text"),
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle button click events."""
        if (event.type == pygame_gui.UI_BUTTON_PRESSED and 
            event.ui_element == self.button):
            return True
        return False


class UnitUpgradeUI(UIWindow):
    """Main UI window for upgrading unit tiers."""
    
    def __init__(self, manager: pygame_gui.UIManager):
        self.manager = manager
        self.selected_unit_type: Optional[UnitType] = None
        self.unit_cards: List[UnitCard] = []
        
        # Calculate window size and position
        screen_info = pygame.display.Info()
        window_width = 1000
        window_height = 700
        window_x = (screen_info.current_w - window_width) // 2
        window_y = (screen_info.current_h - window_height) // 2
        
        super().__init__(
            rect=pygame.Rect((window_x, window_y), (window_width, window_height)),
            window_display_title="Unit Upgrades",
            manager=manager,
            resizable=False
        )
        
        # Get all unlocked units from progress manager
        available_units = progress_manager.available_units(None)
        self.unlocked_units = [unit_type for unit_type, count in available_units.items() if count > 0]
        
        self.create_ui_elements()
    
    def create_ui_elements(self):
        """Create all UI elements."""
        # Currency display at the top
        currency_y = 10
        self.advanced_credits_label = UILabel(
            relative_rect=pygame.Rect((20, currency_y), (200, 30)),
            text=f"Advanced Credits: {progress_manager.advanced_credits}",
            manager=self.manager,
            container=self
        )
        
        self.elite_credits_label = UILabel(
            relative_rect=pygame.Rect((230, currency_y), (200, 30)),
            text=f"Elite Credits: {progress_manager.elite_credits}",
            manager=self.manager,
            container=self
        )
        
        # Unit selection area (scrollable)
        unit_area_y = 50
        unit_area_height = 120
        
        self.unit_scroll_container = UIScrollingContainer(
            relative_rect=pygame.Rect((20, unit_area_y), (960, unit_area_height)),
            manager=self.manager,
            container=self
        )
        
        # Populate units
        self.unit_buttons: List[UnitUpgradeButton] = []
        self.populate_unit_buttons()
        
        # Unit cards area
        cards_y = unit_area_y + unit_area_height + 20
        self.cards_panel = UIPanel(
            relative_rect=pygame.Rect((20, cards_y), (960, 480)),
            manager=self.manager,
            container=self,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        )
        
        # Initially show instruction text
        self.instruction_label = UILabel(
            relative_rect=pygame.Rect((400, 200), (200, 30)),
            text="Select a unit to view upgrade options",
            manager=self.manager,
            container=self.cards_panel
        )
    
    def populate_unit_buttons(self):
        """Create buttons for all unlocked units."""
        x_position = 0
        y_position = 10
        padding = 10
        
        for unit_type in self.unlocked_units:
            button = UnitUpgradeButton(
                x_pos=x_position,
                y_pos=y_position,
                unit_type=unit_type,
                manager=self.manager,
                container=self.unit_scroll_container
            )
            self.unit_buttons.append(button)
            x_position += UnitUpgradeButton.size + padding
        
        # Set the scrollable area size
        total_width = max(x_position, 960)
        self.unit_scroll_container.set_scrollable_area_dimensions((total_width, 100))
    
    def show_unit_cards(self, unit_type: UnitType):
        """Display the three tier cards for the selected unit."""
        # Clear existing cards
        self.clear_unit_cards()
        
        # Hide instruction label
        if hasattr(self, 'instruction_label'):
            self.instruction_label.kill()
        
        # Get unit data
        unit_data = UNIT_DATA.get(unit_type, {})
        unit_name = unit_data.get("name", unit_type.value)
        unit_description = unit_data.get("description", "")
        
        # Create three cards side by side
        card_width = 300
        card_spacing = 20
        start_x = (960 - (3 * card_width + 2 * card_spacing)) // 2
        
        current_tier = progress_manager.get_unit_tier(unit_type)
        
        for i, tier in enumerate([UnitTier.BASIC, UnitTier.ADVANCED, UnitTier.ELITE]):
            card_x = start_x + i * (card_width + card_spacing)
            
            # Modify the title to show tier
            tier_name = f"{unit_name} ({tier.value})"
            
            # Create the card
            card = UnitCard(
                screen=pygame.display.get_surface(),
                manager=self.manager,
                position=(card_x, 10),
                name=tier_name,
                description=unit_description,
                unit_type=unit_type
            )
            
            # Move the card to our container
            card.window.container = self.cards_panel
            card.window.relative_rect.x = card_x
            card.window.relative_rect.y = 10
            
            # Add visual indicators
            if tier == current_tier:
                # Highlight current tier
                card.window.title_bar.background_colour = pygame.Color('#4CAF50')
                card.window.title_bar.rebuild()
            elif tier.value < current_tier.value and tier != UnitTier.ELITE:
                # Darken lower tiers
                card.window.background_colour = pygame.Color('#555555')
                card.window.rebuild()
            
            self.unit_cards.append(card)
        
        # Create upgrade buttons
        self.create_upgrade_buttons(unit_type, current_tier, start_x, card_width, card_spacing)
    
    def create_upgrade_buttons(self, unit_type: UnitType, current_tier: UnitTier, 
                              start_x: int, card_width: int, card_spacing: int):
        """Create upgrade buttons between the cards."""
        # Button between BASIC and ADVANCED
        if current_tier == UnitTier.BASIC:
            button_x = start_x + card_width + (card_spacing - 100) // 2
            can_upgrade = progress_manager.can_upgrade_unit(unit_type)
            
            self.basic_to_advanced_button = UIButton(
                relative_rect=pygame.Rect((button_x, 200), (100, 40)),
                text=f"Upgrade\n1 Adv Credit",
                manager=self.manager,
                container=self.cards_panel
            )
            
            if not can_upgrade:
                self.basic_to_advanced_button.disable()
        
        # Button between ADVANCED and ELITE
        if current_tier == UnitTier.ADVANCED:
            button_x = start_x + 2 * card_width + card_spacing + (card_spacing - 100) // 2
            can_upgrade = progress_manager.can_upgrade_unit(unit_type)
            
            self.advanced_to_elite_button = UIButton(
                relative_rect=pygame.Rect((button_x, 200), (100, 40)),
                text=f"Upgrade\n1 Elite Credit",
                manager=self.manager,
                container=self.cards_panel
            )
            
            if not can_upgrade:
                self.advanced_to_elite_button.disable()
    
    def clear_unit_cards(self):
        """Remove all currently displayed unit cards."""
        for card in self.unit_cards:
            card.kill()
        self.unit_cards.clear()
        
        # Remove upgrade buttons
        if hasattr(self, 'basic_to_advanced_button'):
            self.basic_to_advanced_button.kill()
            delattr(self, 'basic_to_advanced_button')
        
        if hasattr(self, 'advanced_to_elite_button'):
            self.advanced_to_elite_button.kill()
            delattr(self, 'advanced_to_elite_button')
    
    def update_currency_display(self):
        """Update the currency labels."""
        self.advanced_credits_label.set_text(f"Advanced Credits: {progress_manager.advanced_credits}")
        self.elite_credits_label.set_text(f"Elite Credits: {progress_manager.elite_credits}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events."""
        # Check for unit button clicks
        for button in self.unit_buttons:
            if button.handle_event(event):
                self.selected_unit_type = button.unit_type
                self.show_unit_cards(button.unit_type)
                return True
        
        # Check for upgrade button clicks
        if (event.type == pygame_gui.UI_BUTTON_PRESSED and 
            self.selected_unit_type is not None):
            
            if (hasattr(self, 'basic_to_advanced_button') and 
                event.ui_element == self.basic_to_advanced_button):
                if progress_manager.upgrade_unit(self.selected_unit_type):
                    self.update_currency_display()
                    self.show_unit_cards(self.selected_unit_type)  # Refresh display
                    # Update the unit button tier indicator
                    for button in self.unit_buttons:
                        if button.unit_type == self.selected_unit_type:
                            tier = progress_manager.get_unit_tier(self.selected_unit_type)
                            button.tier_label.set_text(tier.value[0])
                            break
                return True
            
            elif (hasattr(self, 'advanced_to_elite_button') and 
                  event.ui_element == self.advanced_to_elite_button):
                if progress_manager.upgrade_unit(self.selected_unit_type):
                    self.update_currency_display()
                    self.show_unit_cards(self.selected_unit_type)  # Refresh display
                    # Update the unit button tier indicator
                    for button in self.unit_buttons:
                        if button.unit_type == self.selected_unit_type:
                            tier = progress_manager.get_unit_tier(self.selected_unit_type)
                            button.tier_label.set_text(tier.value[0])
                            break
                return True
        
        return False
    
    def update(self, time_delta: float):
        """Update the UI."""
        for card in self.unit_cards:
            card.update(time_delta)