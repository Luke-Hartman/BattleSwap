"""UI component for package selection after reclaiming all corrupted maps."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton, UITextBox, UIImage
from typing import List, Optional, Callable, Dict, Union, Tuple

from entities.items import ItemType, item_theme_ids
from components.spell_type import SpellType
from entities.spells import spell_theme_ids
from point_values import item_values, spell_values
from progress_manager import Package
from ui_components.item_card import ItemCard
from ui_components.spell_card import SpellCard
from ui_components.game_data import get_item_data


class PackageSelectionPanel(UIPanel):
    """Panel for selecting a package of items or spells after reclaiming all corrupted maps."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
        packages: List[Package],
        on_selection: Callable[[Package], None]
    ):
        """Initialize the package selection panel.
        
        Args:
            manager: The UI manager.
            packages: List of packages to choose from.
            on_selection: Callback function called when a package is selected.
        """
        self.packages = packages
        self.on_selection = on_selection
        self.selected_package: Optional[Package] = None
        self.manager = manager  # Store manager for card creation
        
        # Panel sized for vertical layout with card slot on top
        panel_width = 340  # Standard width
        panel_height = 610
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        super().__init__(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=manager,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        )
        
        # Create package selection buttons (icon-based)
        self.package_buttons: List[UIButton] = []
        
        # Create card slot panel on top
        card_slot_width = 300  # BaseCard.WIDTH
        card_slot_height = 475  # BaseCard.HEIGHT
        card_slot_x = (panel_width - card_slot_width) // 2  # Center horizontally
        card_slot_y = 20
        
        self.card_slot_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(card_slot_x, card_slot_y, card_slot_width, card_slot_height),
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(object_id='#upgrade_card_panel')
        )
        
        # Initialize card as None
        self.displayed_card: Optional[Union[ItemCard, SpellCard]] = None
        
        # Position icon buttons below the card slot
        icon_size = 80
        button_spacing = 20
        start_x = (panel_width - (len(packages) * icon_size + (len(packages) - 1) * button_spacing)) // 2
        button_y = card_slot_y + card_slot_height + 10  # Position below card slot with 10px gap
        
        for i, package in enumerate(packages):
            button_x = start_x + i * (icon_size + button_spacing)
            
            # Get the theme ID for the first item/spell in the package
            theme_id = self._get_package_theme_id(package)
            
            # Package button with theme-based icon
            button = UIButton(
                relative_rect=pygame.Rect((button_x, button_y), (icon_size, icon_size)),
                text="",  # No text, just icon
                manager=manager,
                container=self,
                object_id=pygame_gui.core.ObjectID(
                    class_id="@package_button",
                    object_id=theme_id
                )
            )
            
            self.package_buttons.append(button)
            
            # No need for hover card placeholders - we use a single card slot
    
    def _get_package_theme_id(self, package: Package) -> str:
        """Get the theme ID for a package based on its contents.
        
        Args:
            package: The package to get a theme ID for.
            
        Returns:
            Theme ID string for the button styling.
        """
        if package.items:
            # Get the first item's theme ID
            item_type = list(package.items.keys())[0]
            return item_theme_ids[item_type]
        elif package.spells:
            # Get the first spell's theme ID
            spell_type = list(package.spells.keys())[0]
            return spell_theme_ids[spell_type]
        raise AssertionError("Package has no items or spells")
    
    def _format_package_description(self, package: Package) -> str:
        """Format a package description for display.
        
        Args:
            package: The package to format.
            
        Returns:
            HTML formatted description string.
        """
        if package.items:
            # Item package
            items_text = []
            for item_type, count in package.items.items():
                item_name = item_type.value.replace('_', ' ').title()
                items_text.append(f"<b>{count}x {item_name}</b>")
            
            return f"<b>Items Package</b><br>" + "<br>".join(items_text)
        else:
            # Spell package
            spells_text = []
            for spell_type, count in package.spells.items():
                spell_name = spell_type.value.replace('_', ' ').title()
                spells_text.append(f"<b>{count}x {spell_name}</b>")
            
            return f"<b>Spells Package</b><br>" + "<br>".join(spells_text)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events.
        
        Args:
            event: The pygame event to handle.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Handle package selection - directly select and close
            for i, button in enumerate(self.package_buttons):
                if event.ui_element == button:
                    self._select_package(i)
                    # Immediately call the selection callback and close panel
                    self.on_selection(self.selected_package)
                    self.kill()
                    return True
        
        # Handle mouse hover for card display
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos  # Use event position instead of pygame.mouse.get_pos()
            hovered_button_index = None
            
            for i, button in enumerate(self.package_buttons):
                if button.rect.collidepoint(mouse_pos):
                    hovered_button_index = i
                    break
            
            # Display card for hovered button
            if hovered_button_index is not None:
                package = self.packages[hovered_button_index]
                self._display_package_card(package)
            else:
                # No button hovered, clear the card slot
                self._clear_card_slot()
        
        # No Enter key handling needed - clicking buttons directly selects
        
        return False
    
    def _select_package(self, package_index: int) -> None:
        """Select a package and update the UI.
        
        Args:
            package_index: Index of the package to select.
        """
        self.selected_package = self.packages[package_index]
        
        # Update button appearances
        for i, button in enumerate(self.package_buttons):
            if i == package_index:
                button.select()
            else:
                button.unselect()
        
        # Display the selected package card
        self._display_package_card(self.selected_package)
    
    def _display_package_card(self, package: Package) -> None:
        """Display a package card in the card slot.
        
        Args:
            package: The package to display
        """
        # Clear any existing card
        self._clear_card_slot()
        
        if package.items:
            # Create ItemCard for the first (and only) item in the package
            item_type = list(package.items.keys())[0]
            self.displayed_card = ItemCard(
                screen=pygame.display.get_surface(),
                manager=self.manager,
                position=(0, 0),  # Position doesn't matter when using container
                item_type=item_type,
                container=self.card_slot_panel,
                padding=10
            )
        else:
            # Create SpellCard for the first (and only) spell in the package
            spell_type = list(package.spells.keys())[0]
            self.displayed_card = SpellCard(
                screen=pygame.display.get_surface(),
                manager=self.manager,
                position=(0, 0),  # Position doesn't matter when using container
                spell_type=spell_type,
                container=self.card_slot_panel,
                padding=10
            )
    
    def _clear_card_slot(self) -> None:
        """Clear the card slot."""
        if self.displayed_card is not None:
            self.displayed_card.kill()
            self.displayed_card = None
    
    def kill(self) -> None:
        """Clean up the panel and displayed card."""
        # Clean up displayed card
        self._clear_card_slot()
        
        # Call parent kill
        super().kill()

