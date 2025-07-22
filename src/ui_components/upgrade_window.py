"""Unit upgrade window UI component."""

import pygame
import pygame_gui
from typing import Optional, Dict, List
from pygame_gui.core import ObjectID

from components.unit_type import UnitType
from components.unit_tier import UnitTier
from entities.units import unit_theme_ids, Faction
from progress_manager import progress_manager
from ui_components.unit_card import UnitCard
from ui_components.game_data import get_unit_data, StatType, get_upgrade_description
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from keyboard_shortcuts import format_button_text, KeyboardShortcuts


class UnitIconButton(pygame_gui.elements.UIButton):
    """A button that displays a unit icon for selection."""
    
    size = 80  # Same size as barracks
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        unit_type: UnitType,
        manager: pygame_gui.UIManager,
        container: Optional[pygame_gui.core.UIContainer] = None,
    ):
        self.unit_type = unit_type
        
        # Get tier-specific theme class for the unit icon
        from progress_manager import progress_manager
        from entities.units import get_unit_icon_theme_class
        unit_tier = progress_manager.get_unit_tier(unit_type)
        tier_theme_class = get_unit_icon_theme_class(unit_tier)
        
        super().__init__(
            relative_rect=pygame.Rect((x_pos, y_pos), (self.size, self.size)),
            text="",
            manager=manager,
            container=container,
            object_id=ObjectID(class_id=tier_theme_class, object_id=unit_theme_ids[unit_type]),
        )
        self.can_hover = lambda: True

    def refresh_tier_styling(self) -> None:
        """Update the tier-specific styling for this unit icon."""
        from progress_manager import progress_manager
        from entities.units import get_unit_icon_theme_class
        unit_tier = progress_manager.get_unit_tier(self.unit_type)
        tier_theme_class = get_unit_icon_theme_class(unit_tier)
        
        # Update the button's object ID with the new tier theme class
        new_object_id = ObjectID(class_id=tier_theme_class, object_id=unit_theme_ids[self.unit_type])
        self.change_object_id(new_object_id)


class UpgradeWindow:
    """A large modal window for upgrading units."""
    
    def __init__(self, manager: pygame_gui.UIManager):
        """Initialize the upgrade window."""
        self.manager = manager
        self.window = None
        self.close_button = None
        self.selected_unit_type: Optional[UnitType] = None
        self.unit_buttons: List[UnitIconButton] = []
        # Initialize upgrade dialogs list
        if not hasattr(self.manager, 'upgrade_dialogs'):
            self.manager.upgrade_dialogs = []
        
        # Initialize description box references
        self.advanced_description_box = None
        self.advanced_description_box_top = None
        self.advanced_description_box_bottom = None
        self.elite_description_box = None
        self.elite_description_box_top = None
        self.elite_description_box_bottom = None
        
        self._create_window()
    
    def _create_window(self) -> None:
        """Create the upgrade window and its contents."""
        # Get screen dimensions
        screen_info = pygame.display.Info()
        screen_width = screen_info.current_w
        screen_height = screen_info.current_h
        
        # Calculate exact content size needed
        self.card_width = 300
        self.card_height = 475
        self.panel_spacing = 20
        self.description_height = 30
        self.description_margin = 5
        self.card_margin = 10 + self.description_height + self.description_margin
        top_section_height = 200
        
        # Content dimensions
        content_width = self.card_width * 3 + self.panel_spacing * 2  # 940px
        content_height = top_section_height + self.card_margin + self.card_height  # 740px
        
        # Window size with minimal margin (5px on all sides, plus window frame)
        window_width = content_width + 16  # 10px margin + 6px for panel borders
        window_height = content_height + 40  # 10px margin + 30px for title bar
        
        # Center the window
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2
        
        # Create the main window
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(window_x, window_y, window_width, window_height),
            manager=self.manager,
            window_display_title="Unit Upgrades",
            resizable=True,
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
        
        # Create top section (unit selection)
        top_section = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(3, 3, window_width - 6, top_section_height - 3),
            manager=self.manager,
            container=self.window,
            anchors={'left': 'left',
                    'right': 'right',
                    'top': 'top',
                    'bottom': 'top'}
        )
        
        # Create scrolling container for unit grid
        scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect(0, 0, window_width - 6, top_section_height - 6),
            manager=self.manager,
            container=top_section,
            allow_scroll_y=True,
            allow_scroll_x=False
        )
        self.scroll_container = scroll_container  # Store reference for event handling
        
        # Create unit grid in scrolling container
        self._create_unit_grid(scroll_container, window_width - 12, top_section_height - 12)
        
        # Create bottom section (upgrade details)
        bottom_section = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(3, top_section_height, window_width - 6, window_height - top_section_height - 30),
            manager=self.manager,
            container=self.window,
            anchors={'left': 'left',
                    'right': 'right',
                    'top': 'top',
                    'bottom': 'bottom'},
            object_id=ObjectID(object_id='#upgrade_bottom_section')
        )
        self.bottom_section = bottom_section  # Store reference for later use
        
        # Create three panels for unit cards (Basic, Advanced, Elite)
        total_width = self.card_width * 3 + self.panel_spacing * 2
        self.start_x = (window_width - 6 - total_width) // 2  # Center the cards
        
        self.basic_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.start_x, self.card_margin, self.card_width, self.card_height),
            manager=self.manager,
            container=bottom_section,
            object_id=ObjectID(object_id='#upgrade_card_panel')
        )
        
        # Create initial single description labels for Advanced and Elite tiers
        self._create_description_labels()
        
        self.advanced_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.start_x + self.card_width + self.panel_spacing, self.card_margin, self.card_width, self.card_height),
            manager=self.manager,
            container=bottom_section,
            object_id=ObjectID(object_id='#upgrade_card_panel')
        )
        
        self.elite_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.start_x + (self.card_width + self.panel_spacing) * 2, self.card_margin, self.card_width, self.card_height),
            manager=self.manager,
            container=bottom_section,
            object_id=ObjectID(object_id='#upgrade_card_panel')
        )
        
        # Initialize unit cards as None
        self.basic_card = None
        self.advanced_card = None
        self.elite_card = None
        
        # Add upgrade button and credit display above the basic card (where basic description would go)
        controls_y = self.card_margin - self.description_height - self.description_margin
        
        # Add credit display on the left (two separate labels)
        self.advanced_credit_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.start_x, controls_y - 12, 150, self.description_height),
            text="",
            manager=self.manager,
            container=bottom_section
        )
        
        self.elite_credit_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.start_x, controls_y + 8, 150, self.description_height),
            text="",
            manager=self.manager,
            container=bottom_section
        )
        
        # Add upgrade button on the right
        upgrade_button_width = 140
        upgrade_button_x = self.start_x + self.card_width - upgrade_button_width
        self.upgrade_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(upgrade_button_x, controls_y, upgrade_button_width, self.description_height),
            text=format_button_text("Upgrade", KeyboardShortcuts.ENTER),
            manager=self.manager,
            container=bottom_section,
            anchors={'left': 'left',
                    'right': 'left',
                    'top': 'top',
                    'bottom': 'top'}
        )
        self.upgrade_button.disable()  # Start disabled until a unit is selected
        self.upgrade_button.set_tooltip("Select a unit to upgrade")
        self._update_credit_display()
    
    def _create_description_labels(self) -> None:
        """Create the initial single description labels for Advanced and Elite tiers."""
        # Clear existing labels
        self._clear_description_labels()
        
        # Create single description labels (default state)
        self.advanced_description_box = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.start_x + self.card_width + self.panel_spacing, self.card_margin - self.description_height - self.description_margin, self.card_width, self.description_height),
            text="",
            manager=self.manager,
            container=self.bottom_section,
            object_id=ObjectID(object_id='#upgrade_description_label')
        )
        
        self.elite_description_box = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.start_x + (self.card_width + self.panel_spacing) * 2, self.card_margin - self.description_height - self.description_margin, self.card_width, self.description_height),
            text="",
            manager=self.manager,
            container=self.bottom_section,
            object_id=ObjectID(object_id='#upgrade_description_label')
        )
    
    def _clear_description_labels(self) -> None:
        """Clear all description labels."""
        # Clear single labels
        if self.advanced_description_box:
            self.advanced_description_box.kill()
            self.advanced_description_box = None
        if self.elite_description_box:
            self.elite_description_box.kill()
            self.elite_description_box = None
        
        # Clear dual labels
        if self.advanced_description_box_top:
            self.advanced_description_box_top.kill()
            self.advanced_description_box_top = None
        if self.advanced_description_box_bottom:
            self.advanced_description_box_bottom.kill()
            self.advanced_description_box_bottom = None
        if self.elite_description_box_top:
            self.elite_description_box_top.kill()
            self.elite_description_box_top = None
        if self.elite_description_box_bottom:
            self.elite_description_box_bottom.kill()
            self.elite_description_box_bottom = None
    
    def _create_dual_description_labels(self, tier: str, x_pos: int, text_lines: List[str]) -> None:
        """Create dual description labels for a tier."""
        label_height = 20  # Each label gets 20px height
        base_y = self.card_margin - self.description_height - self.description_margin - 8
        
        if tier == "advanced":
            self.advanced_description_box_top = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(x_pos, base_y, self.card_width, label_height),
                text=text_lines[0],
                manager=self.manager,
                container=self.bottom_section,
                object_id=ObjectID(object_id='#upgrade_description_label')
            )
            
            self.advanced_description_box_bottom = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(x_pos, base_y + label_height, self.card_width, label_height),
                text=text_lines[1],
                manager=self.manager,
                container=self.bottom_section,
                object_id=ObjectID(object_id='#upgrade_description_label')
            )
        elif tier == "elite":
            self.elite_description_box_top = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(x_pos, base_y, self.card_width, label_height),
                text=text_lines[0],
                manager=self.manager,
                container=self.bottom_section,
                object_id=ObjectID(object_id='#upgrade_description_label')
            )
            
            self.elite_description_box_bottom = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(x_pos, base_y + label_height, self.card_width, label_height),
                text=text_lines[1],
                manager=self.manager,
                container=self.bottom_section,
                object_id=ObjectID(object_id='#upgrade_description_label')
            )
    
    def _update_description_labels(self, tier: str, text: str, x_pos: int) -> None:
        """Update description labels for a tier, handling single or dual line text."""
        # Check if text contains newlines (indicating two lines)
        if '\n' in text:
            lines = text.split('\n', 1)  # Split into max 2 parts
            if len(lines) == 2:
                # Clear single label for this tier
                if tier == "advanced" and self.advanced_description_box:
                    self.advanced_description_box.kill()
                    self.advanced_description_box = None
                elif tier == "elite" and self.elite_description_box:
                    self.elite_description_box.kill()
                    self.elite_description_box = None
                
                # Create dual labels
                self._create_dual_description_labels(tier, x_pos, lines)
            else:
                # Fallback to single label
                self._set_single_description_label(tier, text, x_pos)
        else:
            # Single line text - ensure we have single label
            self._set_single_description_label(tier, text, x_pos)
    
    def _set_single_description_label(self, tier: str, text: str, x_pos: int) -> None:
        """Set text for single description label, creating it if needed."""
        if tier == "advanced":
            # Clear dual labels if they exist
            if self.advanced_description_box_top:
                self.advanced_description_box_top.kill()
                self.advanced_description_box_top = None
            if self.advanced_description_box_bottom:
                self.advanced_description_box_bottom.kill()
                self.advanced_description_box_bottom = None
            
            # Create or update single label
            if not self.advanced_description_box:
                self.advanced_description_box = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(x_pos, self.card_margin - self.description_height - self.description_margin, self.card_width, self.description_height),
                    text=text,
                    manager=self.manager,
                    container=self.bottom_section,
                    object_id=ObjectID(object_id='#upgrade_description_label')
                )
            else:
                self.advanced_description_box.set_text(text)
        
        elif tier == "elite":
            # Clear dual labels if they exist
            if self.elite_description_box_top:
                self.elite_description_box_top.kill()
                self.elite_description_box_top = None
            if self.elite_description_box_bottom:
                self.elite_description_box_bottom.kill()
                self.elite_description_box_bottom = None
            
            # Create or update single label
            if not self.elite_description_box:
                self.elite_description_box = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(x_pos, self.card_margin - self.description_height - self.description_margin, self.card_width, self.description_height),
                    text=text,
                    manager=self.manager,
                    container=self.bottom_section,
                    object_id=ObjectID(object_id='#upgrade_description_label')
                )
            else:
                self.elite_description_box.set_text(text)
    
    def _select_unit(self, unit_type: UnitType) -> None:
        """Select a unit and update the UI accordingly."""
        # Unselect all other buttons
        for button in self.unit_buttons:
            if button.unit_type != unit_type:
                button.unselect()
            else:
                button.select()
        
        self.selected_unit_type = unit_type
        self._update_upgrade_details()
        self._update_upgrade_button_state()
        self._update_credit_display()
    
    def _create_unit_grid(self, container: pygame_gui.elements.UIPanel, container_width: int, container_height: int) -> None:
        """Create a grid of unit icons in the given container."""
        # Get available units from progress manager
        available_units = set(progress_manager.available_units(None))
        
        assert available_units, "No units available for upgrade"
        
        # Auto-unlock basic zombies for upgrading when any zombie unit is available
        zombie_units = {
            UnitType.ZOMBIE_BASIC_ZOMBIE,
            UnitType.ZOMBIE_BRUTE,
            UnitType.ZOMBIE_GRABBER,
            UnitType.ZOMBIE_JUMPER,
            UnitType.ZOMBIE_SPITTER,
            UnitType.ZOMBIE_TANK
        }
            
        # Check if any zombie unit is available
        if available_units & zombie_units:
            available_units.add(UnitType.ZOMBIE_BASIC_ZOMBIE)
        
        # Calculate grid layout
        icon_size = UnitIconButton.size
        padding = 5  # Reduced from 10 to 5
        icons_per_row = max(1, (container_width - padding) // (icon_size + padding))
        
        # Create unit buttons in a grid
        row = 0
        col = 0
        y_offset = 10  # Start with small padding from top
        
        for unit_type in sorted(available_units, key=lambda x: x.value):
            x_pos = col * (icon_size + padding) + padding
            y_pos = row * (icon_size + padding) + y_offset
            
            unit_button = UnitIconButton(
                x_pos=x_pos,
                y_pos=y_pos,
                unit_type=unit_type,
                manager=self.manager,
                container=container
            )
            self.unit_buttons.append(unit_button)
            
            # Move to next position
            col += 1
            if col >= icons_per_row:
                col = 0
                row += 1
    
    def _update_upgrade_details(self) -> None:
        """Update the upgrade details section based on selected unit."""
        if self.selected_unit_type is None:
            # Clear any existing cards
            self._clear_unit_cards()
            # Recreate panels with default theme
            self._recreate_panels_with_theme('#upgrade_card_panel')
            # Clear description labels
            self._clear_description_labels()
            self._create_description_labels()
            return
        
        # Clear existing cards
        self._clear_unit_cards()
        
        # Get current tier of the selected unit
        current_tier = progress_manager.get_unit_tier(self.selected_unit_type)
        
        # Determine which panel should have the current tier theme
        current_theme = '#upgrade_card_panel_current'
        default_theme = '#upgrade_card_panel'
        
        if current_tier == UnitTier.BASIC:
            self._recreate_panels_with_theme(default_theme, basic_theme=current_theme)
        elif current_tier == UnitTier.ADVANCED:
            self._recreate_panels_with_theme(default_theme, advanced_theme=current_theme)
        elif current_tier == UnitTier.ELITE:
            self._recreate_panels_with_theme(default_theme, elite_theme=current_theme)
        else:
            self._recreate_panels_with_theme(default_theme)
        
        # Update upgrade description labels
        advanced_description = get_upgrade_description(self.selected_unit_type, UnitTier.ADVANCED)
        elite_description = get_upgrade_description(self.selected_unit_type, UnitTier.ELITE)
        
        # Update advanced description
        advanced_x = self.start_x + self.card_width + self.panel_spacing
        self._update_description_labels("advanced", advanced_description, advanced_x)
        
        # Update elite description
        elite_x = self.start_x + (self.card_width + self.panel_spacing) * 2
        self._update_description_labels("elite", elite_description, elite_x)
        
        # Create unit cards for each tier
        self._create_unit_cards()
    
    def _create_unit_cards(self) -> None:
        """Create unit cards for all three tiers."""
        if self.selected_unit_type is None:
            return
        
        # Create Basic tier card
        basic_data = get_unit_data(self.selected_unit_type, UnitTier.BASIC)
        self.basic_card = UnitCard(
            screen=pygame.display.get_surface(),
            manager=self.manager,
            position=(0, 0),  # Position doesn't matter when using container
            name=basic_data.name,
            description=basic_data.description,
            unit_type=self.selected_unit_type,
            unit_tier=UnitTier.BASIC,
            container=self.basic_panel,
            padding=10
        )
        
        # Add stats to basic card
        for stat_type in StatType:
            stat_value = basic_data.stats[stat_type]
            if stat_value is not None:
                self.basic_card.add_stat(
                    stat_type=stat_type,
                    value=int(stat_value),
                    tooltip_text=basic_data.tooltips[stat_type] or "N/A",
                    modification_level=basic_data.modification_levels.get(stat_type, 0)
                )
            else:
                self.basic_card.skip_stat(stat_type=stat_type)
        
        # Create Advanced tier card
        advanced_data = get_unit_data(self.selected_unit_type, UnitTier.ADVANCED)
        self.advanced_card = UnitCard(
            screen=pygame.display.get_surface(),
            manager=self.manager,
            position=(0, 0),
            name=advanced_data.name,
            description=advanced_data.description,
            unit_type=self.selected_unit_type,
            unit_tier=UnitTier.ADVANCED,
            container=self.advanced_panel,
            padding=10
        )
        
        # Add stats to advanced card
        for stat_type in StatType:
            stat_value = advanced_data.stats[stat_type]
            if stat_value is not None:
                self.advanced_card.add_stat(
                    stat_type=stat_type,
                    value=int(stat_value),
                    tooltip_text=advanced_data.tooltips[stat_type] or "N/A",
                    modification_level=advanced_data.modification_levels.get(stat_type, 0)
                )
            else:
                self.advanced_card.skip_stat(stat_type=stat_type)
        
        # Create Elite tier card
        elite_data = get_unit_data(self.selected_unit_type, UnitTier.ELITE)
        self.elite_card = UnitCard(
            screen=pygame.display.get_surface(),
            manager=self.manager,
            position=(0, 0),
            name=elite_data.name,
            description=elite_data.description,
            unit_type=self.selected_unit_type,
            unit_tier=UnitTier.ELITE,
            container=self.elite_panel,
            padding=10
        )
        
        # Add stats to elite card
        for stat_type in StatType:
            stat_value = elite_data.stats[stat_type]
            if stat_value is not None:
                self.elite_card.add_stat(
                    stat_type=stat_type,
                    value=int(stat_value),
                    tooltip_text=elite_data.tooltips[stat_type] or "N/A",
                    modification_level=elite_data.modification_levels.get(stat_type, 0)
                )
            else:
                self.elite_card.skip_stat(stat_type=stat_type)
    
    def update(self, time_delta: float) -> None:
        """Update the upgrade window and its unit cards."""
        # Update unit cards if they exist
        if self.basic_card:
            self.basic_card.update(time_delta)
        if self.advanced_card:
            self.advanced_card.update(time_delta)
        if self.elite_card:
            self.elite_card.update(time_delta)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for the upgrade window. Returns True if event was handled."""
        # For scroll wheel events, process pygame_gui events first to allow scrolling container to work
        if event.type == pygame.MOUSEWHEEL:
            # Check if mouse is over the upgrade window
            if self.window and self.window.get_abs_rect().collidepoint(pygame.mouse.get_pos()):
                # Let pygame_gui process the event first to handle scrolling
                self.manager.process_events(event)
                # Always consume the event to prevent it from reaching the camera
                return True
        
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            # Handle Enter key
            if event.key == pygame.K_RETURN:
                # Check if we have an active upgrade dialog
                if hasattr(self.manager, 'upgrade_dialogs') and self.manager.upgrade_dialogs:
                    # Simulate clicking the confirm button on the first dialog
                    dialog = self.manager.upgrade_dialogs[0]
                    pygame.event.post(pygame.event.Event(
                        pygame.USEREVENT,
                        {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': dialog.confirm_button}
                    ))
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.5
                    ))
                    return True
                # If no dialog is open, check if we can trigger the upgrade button
                elif self.upgrade_button and self.upgrade_button.is_enabled:
                    pygame.event.post(pygame.event.Event(
                        pygame.USEREVENT,
                        {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': self.upgrade_button}
                    ))
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.5
                    ))
                    return True
                    
            # Handle Escape key for confirmation dialogs only
            elif event.key == pygame.K_ESCAPE:
                # Check if we have an active upgrade dialog
                if hasattr(self.manager, 'upgrade_dialogs') and self.manager.upgrade_dialogs:
                    # Simulate clicking the cancel button on the first dialog
                    dialog = self.manager.upgrade_dialogs[0]
                    pygame.event.post(pygame.event.Event(
                        pygame.USEREVENT,
                        {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': dialog.cancel_button}
                    ))
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.5
                    ))
                    return True
                # If no dialog is open, don't consume the escape key (let it bubble up to close the window)
                
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.close_button:
                    self.kill()
                    return True
                
                # Handle unit selection
                for unit_button in self.unit_buttons:
                    if event.ui_element == unit_button:
                        self._select_unit(unit_button.unit_type)
                        return True
                
                # Handle upgrade button click
                if event.ui_element == self.upgrade_button:
                    self._show_upgrade_confirmation()
                    return True
                
                # Handle upgrade dialog events
                if hasattr(self.manager, 'upgrade_dialogs'):
                    for dialog in self.manager.upgrade_dialogs[:]:  # Copy list to avoid modification during iteration
                        if event.ui_element == dialog.confirm_button:
                            # Perform the upgrade
                            success = dialog.progress_manager.upgrade_unit(dialog.unit_type)
                            if success:
                                # Close the dialog
                                dialog.kill()
                                self.manager.upgrade_dialogs.remove(dialog)
                                # Refresh the upgrade details
                                self._update_upgrade_details()
                                self._update_upgrade_button_state()
                                self._update_credit_display()
                                # Refresh unit icon styling for tier changes
                                self.refresh_all_unit_icon_styling()
                                return True
                        elif event.ui_element == dialog.cancel_button:
                            # Close the dialog without upgrading
                            dialog.kill()
                            self.manager.upgrade_dialogs.remove(dialog)
                            return True
                
                # Handle unit card events (tips, upgrade buttons)
                if self.basic_card:
                    if self.basic_card.process_event(event):
                        return True
                if self.advanced_card:
                    if self.advanced_card.process_event(event):
                        return True
                if self.elite_card:
                    if self.elite_card.process_event(event):
                        return True
        
        return False
    
    def kill(self) -> None:
        """Clean up the upgrade window."""
        # Clean up unit cards
        self._clear_unit_cards()
        
        if self.window is not None:
            self.window.kill()
            self.window = None
        if self.close_button is not None:
            self.close_button.kill()
            self.close_button = None
        # Clean up unit buttons
        for button in self.unit_buttons:
            button.kill()
        self.unit_buttons.clear()
        
        # Clean up upgrade button and credit labels
        if self.upgrade_button:
            self.upgrade_button.kill()
        if self.advanced_credit_label:
            self.advanced_credit_label.kill()
        if self.elite_credit_label:
            self.elite_credit_label.kill()
        
        # Clean up description labels
        self._clear_description_labels()
        
        # Clean up scroll container reference
        self.scroll_container = None
    
    def _update_credit_display(self) -> None:
        """Update the credit display based on the selected unit."""
        # Show available credits using the new calculation method
        available_advanced, available_elite = progress_manager.calculate_available_credits()
        self.advanced_credit_label.set_text(f"Advanced: {available_advanced}")
        self.elite_credit_label.set_text(f"Elite: {available_elite}")
    
    def _update_upgrade_button_state(self) -> None:
        """Update the upgrade button state based on selected unit and available credits."""
        if self.selected_unit_type is None:
            self.upgrade_button.disable()
            self.upgrade_button.set_tooltip("Select a unit to upgrade")
            return
        
        current_tier = progress_manager.get_unit_tier(self.selected_unit_type)
        
        # Check if unit can be upgraded
        if current_tier == UnitTier.ELITE:
            self.upgrade_button.disable()
            self.upgrade_button.set_tooltip("Unit is already at maximum tier")
        elif not progress_manager.can_upgrade_unit(self.selected_unit_type):
            self.upgrade_button.disable()
            if current_tier == UnitTier.BASIC:
                self.upgrade_button.set_tooltip("Not enough Advanced credits")
            else:  # current_tier == UnitTier.ADVANCED
                self.upgrade_button.set_tooltip("Not enough Elite credits")
        else:
            next_tier = UnitTier.ADVANCED if current_tier == UnitTier.BASIC else UnitTier.ELITE
            self.upgrade_button.enable()
            self.upgrade_button.set_tooltip(f"Upgrade to {next_tier.value}")
    
    def _show_upgrade_confirmation(self) -> None:
        """Show a confirmation dialog for upgrading the selected unit."""
        if self.selected_unit_type is None:
            return
        
        # Create confirmation dialog
        screen_info = pygame.display.Info()
        dialog_width = 200
        dialog_height = 150  # Increased to accommodate title bar and buttons
        dialog_x = (screen_info.current_w - dialog_width) // 2
        dialog_y = (screen_info.current_h - dialog_height) // 2
        
        # Create the dialog window
        dialog = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height),
            manager=self.manager,
            window_display_title="Confirm",
            resizable=False
        )
        
        # Add simple question text - centered with less margin
        question_text = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 30, dialog_width, 30),
            text="Are you sure?",
            manager=self.manager,
            container=dialog
        )
        
        # Add confirm and cancel buttons - positioned higher up
        confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 80, 85, 30),
            text=format_button_text("Yes", KeyboardShortcuts.ENTER),
            manager=self.manager,
            container=dialog
        )
        
        cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(105, 80, 85, 30),
            text=format_button_text("No", KeyboardShortcuts.ESCAPE),
            manager=self.manager,
            container=dialog
        )
        
        # Store references for event handling
        dialog.confirm_button = confirm_button
        dialog.cancel_button = cancel_button
        dialog.unit_type = self.selected_unit_type
        dialog.progress_manager = progress_manager
        
        # Show the dialog
        dialog.show()
        
        # Add to upgrade dialogs list
        self.manager.upgrade_dialogs.append(dialog)

    def _recreate_panels_with_theme(self, theme: str, basic_theme: str = '', advanced_theme: str = '', elite_theme: str = '') -> None:
        """Recreate panels with the specified theme."""
        # Kill existing panels
        if self.basic_panel:
            self.basic_panel.kill()
        if self.advanced_panel:
            self.advanced_panel.kill()
        if self.elite_panel:
            self.elite_panel.kill()
        
        # Use the stored bottom section reference
        bottom_section = self.bottom_section
        
        # Use the specified themes or default to the main theme
        basic_theme_id = ObjectID(object_id=basic_theme) if basic_theme else ObjectID(object_id=theme)
        advanced_theme_id = ObjectID(object_id=advanced_theme) if advanced_theme else ObjectID(object_id=theme)
        elite_theme_id = ObjectID(object_id=elite_theme) if elite_theme else ObjectID(object_id=theme)
        
        # Use stored positioning values from _create_window
        self.basic_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.start_x, self.card_margin, self.card_width, self.card_height),
            manager=self.manager,
            container=bottom_section,
            object_id=basic_theme_id
        )
        
        self.advanced_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.start_x + self.card_width + self.panel_spacing, self.card_margin, self.card_width, self.card_height),
            manager=self.manager,
            container=bottom_section,
            object_id=advanced_theme_id
        )
        
        self.elite_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(self.start_x + (self.card_width + self.panel_spacing) * 2, self.card_margin, self.card_width, self.card_height),
            manager=self.manager,
            container=bottom_section,
            object_id=elite_theme_id
        ) 

    def refresh_all_unit_icon_styling(self) -> None:
        """Refresh tier-specific styling for all unit icon buttons."""
        for unit_button in self.unit_buttons:
            unit_button.refresh_tier_styling()
    
    def _clear_unit_cards(self) -> None:
        """Clear all unit cards."""
        if self.basic_card is not None:
            self.basic_card.kill()
            self.basic_card = None
        if self.advanced_card is not None:
            self.advanced_card.kill()
            self.advanced_card = None
        if self.elite_card is not None:
            self.elite_card.kill()
            self.elite_card = None 