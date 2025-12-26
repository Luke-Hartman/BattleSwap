"""UI component for package selection after reclaiming all corrupted maps."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton
from typing import Callable, List, Optional, Union

from components.item import ItemType
from entities.items import item_theme_ids
from components.spell_type import SpellType
from entities.spells import spell_theme_ids
from point_values import item_values, spell_values
from progress_manager import Package
from ui_components.item_card import ItemCard
from ui_components.spell_card import SpellCard
from ui_components.item_count import ItemCount
from ui_components.spell_count import SpellCount


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
        self.confirmed = False
        self._displayed_package_index: Optional[int] = None
        
        # Panel sized for vertical layout with card slot on top
        panel_width = 420
        panel_height = 730
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
        
        # Title
        UILabel(
            relative_rect=pygame.Rect((0, 10), (panel_width, 60)),
            text="Choose a Reward",
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )
        
        # Create package selection buttons using count buttons
        self.package_buttons: List[Union[ItemCount, SpellCount]] = []
        
        # Create card slot panel on top
        card_slot_width = 300  # BaseCard.WIDTH
        card_slot_height = 475  # BaseCard.HEIGHT
        card_slot_x = (panel_width - card_slot_width) // 2  # Center horizontally
        card_slot_y = 80
        
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
            
            # Create count button for the package
            hotkey = str(i + 1) if i < 3 else None  # Hotkeys 1-3
            
            if package.items:
                # Create ItemCount for item package
                item_type = list(package.items.keys())[0]
                quantity = package.items[item_type]
                button = ItemCount(
                    x_pos=button_x,
                    y_pos=button_y,
                    item_type=item_type,
                    count=quantity,
                    interactive=True,
                    manager=manager,
                    container=self,
                    hotkey=hotkey
                )
            else:
                # Create SpellCount for spell package
                spell_type = list(package.spells.keys())[0]
                quantity = package.spells[spell_type]
                button = SpellCount(
                    x_pos=button_x,
                    y_pos=button_y,
                    spell_type=spell_type,
                    count=quantity,
                    interactive=True,
                    manager=manager,
                    container=self,
                    hotkey=hotkey
                )
            
            self.package_buttons.append(button)
            
            # No need for hover card placeholders - we use a single card slot

        confirm_button_width = 200
        confirm_button_height = 44
        confirm_x = (panel_width - confirm_button_width) // 2
        confirm_y = button_y + icon_size + 10
        self.confirm_button = UIButton(
            relative_rect=pygame.Rect((confirm_x, confirm_y), (confirm_button_width, confirm_button_height)),
            text="Confirm (Space)",
            manager=manager,
            container=self,
        )
        self.confirm_button.disable()
    
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
        # Handle keyboard shortcuts (1-3)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 and len(self.packages) > 0:
                self._select_package(0)
                return True
            elif event.key == pygame.K_2 and len(self.packages) > 1:
                self._select_package(1)
                return True
            elif event.key == pygame.K_3 and len(self.packages) > 2:
                self._select_package(2)
                return True
            elif event.key == pygame.K_SPACE:
                if self.selected_package is not None:
                    self._confirm_selection()
                return True
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.confirm_button:
                if self.selected_package is not None:
                    self._confirm_selection()
                return True

            # Handle package selection - select only (confirmation is separate)
            for i, button in enumerate(self.package_buttons):
                if event.ui_element == button.button:  # Count buttons have a .button attribute
                    self._select_package(i)
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
                self._display_package_card(package, package_index=hovered_button_index)
            else:
                # If a selection exists, keep showing it; otherwise clear the card slot.
                if self.selected_package is not None:
                    selected_index = self.packages.index(self.selected_package)
                    self._display_package_card(self.selected_package, package_index=selected_index)
                else:
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
                button.button.select()
            else:
                button.button.unselect()
        
        # Display the selected package card
        self._display_package_card(self.selected_package, package_index=package_index)
        self.confirm_button.enable()

    def _confirm_selection(self) -> None:
        """Confirm the current selection, invoke callback, and close the panel."""
        if self.selected_package is None:
            return
        self.confirmed = True
        self.on_selection(self.selected_package)
        self.kill()
    
    def _display_package_card(self, package: Package, package_index: int) -> None:
        """Display a package card in the card slot.
        
        Args:
            package: The package to display.
            package_index: Index of the package being displayed.
        """
        if self._displayed_package_index == package_index:
            return
        self._displayed_package_index = package_index

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
        self._displayed_package_index = None
    
    def kill(self) -> None:
        """Clean up the panel and displayed card."""
        # Clean up count buttons
        for button in self.package_buttons:
            button.kill()

        self.confirm_button.kill()
        
        # Clean up displayed card
        self._clear_card_slot()
        
        # Call parent kill
        super().kill()

