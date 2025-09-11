import pygame
import pygame_gui
import pygame_gui.core
from typing import List, Tuple, Optional
from ui_components.stat_bar import StatBar
from components.unit_type import UnitType
from entities.units import Faction, get_unit_sprite_sheet
from ui_components.game_data import StatType, get_unit_data, UnitTier
from unit_values import unit_values
from pygame_gui.elements import UILabel, UIButton, UIImage, UIPanel
from pygame_gui.core import ObjectID
from info_mode_manager import info_mode_manager
from ui_components.glossary_entry import GlossaryEntry
from components.animation import AnimationType
from game_constants import gc

class UnitCard:
    """A UI component that displays a unit card with a name, description, and stats."""
    
    def __init__(self, 
                 screen: pygame.Surface,
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 name: str,
                 description: str,
                 unit_type: UnitType,
                 unit_tier: UnitTier = UnitTier.BASIC,
                 container: Optional[pygame_gui.core.UIContainer] = None,
                 padding: int = 0):
        """
        Initialize a UnitCard component.
        
        Args:
            screen: The pygame surface
            manager: The UI manager for this component
            position: The (x, y) position to place the window (ignored if container is provided)
            name: The name of the unit
            description: The HTML description of the unit (can include links)
            unit_type: The type of unit to display the image for
            unit_tier: The tier of the unit (Basic, Advanced, Elite)
            container: Optional container to place the card in (if None, creates a window)
            padding: Padding around the unit card
        """
        self.screen = screen
        self.manager = manager
        self.name = name
        self.stat_bars: List[StatBar] = []
        self.unit_type = unit_type
        self.unit_tier = unit_tier
        self.container = container
        self.padding = padding
        
        # Get unit data for this tier
        self.unit_data = get_unit_data(unit_type, unit_tier)
        
        # Add creation_index for positioning system
        self.creation_index: int = 0
        
        # Create window title with tier information
        faction_name = Faction.faction_of(unit_type).name.title()
        window_title = name
        
        # Create the window or use the provided container
        if container is None:
            # Create a window if no container provided
            self.window = pygame_gui.elements.UIWindow(
                rect=pygame.Rect(position, (300, 475)),
                window_display_title=window_title,
                manager=manager,
                resizable=False
            )
            self.card_container = self.window
        else:
            # Use the provided container
            self.window = None
            self.card_container = container
        
        # Adjust sizes for padding
        card_width = 300 - 2 * self.padding
        card_height_top = 200  # Height of image area remains 200
        # Create a surface for the unit display area
        unit_display_surface = pygame.Surface((card_width, card_height_top))
        unit_display_surface.fill(gc.MAP_BATTLEFIELD_COLOR)
        
        # Add the unit display as a UIImage
        self.unit_display = UIImage(
            relative_rect=pygame.Rect((self.padding, self.padding), (card_width, card_height_top)),
            image_surface=unit_display_surface,
            manager=manager,
            container=self.card_container
        )
        
        # Add point value box in upper right corner
        point_value = unit_values.get(unit_type, 0)
        point_value_text = str(point_value)
        
        # Calculate box size based on text
        box_width = 40
        box_height = 25
        
        # Create a background panel for the point value (touching top right corner)
        self.point_value_bg = UIPanel(
            relative_rect=pygame.Rect((300 - box_width - self.padding, self.padding), (box_width, box_height)),
            manager=manager,
            container=self.card_container,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0},
            object_id=ObjectID(object_id='#point_value_box')
        )
        
        # Add the point value text
        self.point_value_label = UILabel(
            relative_rect=pygame.Rect((0, 0), (box_width, box_height)),
            text=point_value_text,
            manager=manager,
            container=self.point_value_bg
        )
        # Add faction label in upper left corner
        self.faction_label = UILabel(
            relative_rect=pygame.Rect((self.padding + 10, self.padding + 5), (150, 20)),
            text=f"Faction: {faction_name}",
            manager=manager,
            container=self.card_container,
            object_id=ObjectID(class_id='@left_aligned_text')
        )
        
        # Add tier label below faction label with tier-specific color
        from entities.units import get_tier_label_theme_class
        tier_theme_class = get_tier_label_theme_class(unit_tier)
        self.tier_label = UILabel(
            relative_rect=pygame.Rect((self.padding + 10, self.padding + 25), (150, 20)),
            text=f"Tier: {unit_tier.value}",
            manager=manager,
            container=self.card_container,
            object_id=ObjectID(class_id=tier_theme_class)
        )
        
        # Add description
        full_description = f"{description}"
        
        # Add unit description with clickable links
        self.text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((self.padding, self.padding + 200), (card_width, 90)),
            html_text=full_description,
            manager=manager,
            container=self.card_container
        )
        
        # Store the window reference in the text box's container for link handling
        if self.window is not None:
            self.text.ui_container.window = self.window
        elif hasattr(container, 'window'):
            self.text.ui_container.window = container.window

        # Add bottom row with label and Tips button
        bottom_y = 410 + self.padding  # Move down if padding at top
        self.bottom_label = UILabel(
            relative_rect=pygame.Rect((self.padding + 10, bottom_y), (180, 30)),
            text="",
            manager=manager,
            container=self.card_container
        )
        self.tips_button = UIButton(
            relative_rect=pygame.Rect((300 - 90 - self.padding, bottom_y), (80, 30)),
            text="Tips",
            manager=manager,
            container=self.card_container
        )
        self.sprite_sheet = get_unit_sprite_sheet(unit_type, tier=unit_tier)
        
        # Animation state tracking
        self.animation_time = 0.0
        self.current_frame = 0
        
        # Flash animation state
        self.flash_time = 0.0
        self.flash_duration = 1.0  # Total flash duration in seconds
        self.flash_alternations = 6  # Number of border switches (3 full cycles)
        self.flash_interval = self.flash_duration / self.flash_alternations
        self.is_flashing = False
        self.flash_state = False  # False = normal, True = flash theme
        
        # Update the unit display with sprite sheet animation
        self.update_unit_display()
    
    def update_unit_display(self):
        """Update the unit display surface with the current sprite frame."""
        # Create a new surface for the display
        display_surface = pygame.Surface((300, 200), pygame.SRCALPHA)
        display_surface.fill(gc.MAP_BATTLEFIELD_COLOR)
        
        # Update the sprite sheet frame
        self.sprite_sheet.update_frame(AnimationType.IDLE, self.current_frame)
        
        # Get the dimensions after scaling
        sprite_width = self.sprite_sheet.rect.width
        sprite_height = self.sprite_sheet.rect.height
        
        # Calculate position to center the sprite in the display area
        center_x = 150  # Center of 300px width
        center_y = 100  # Center of 200px height
        
        # Calculate the top-left position for blitting
        # The sprite's rect.center is already adjusted by sprite_center_offset
        blit_x = center_x - sprite_width // 2 + self.sprite_sheet.sprite_center_offset[0]
        blit_y = center_y - sprite_height // 2 + self.sprite_sheet.sprite_center_offset[1]
        
        # Blit the sprite onto the display surface
        display_surface.blit(self.sprite_sheet.image, (blit_x, blit_y))
        
        # Update the UIImage with the new surface
        self.unit_display.set_image(display_surface)
    
    def add_stat(self, stat_type: StatType, value: int, tooltip_text: str, modification_level: int = 0):
        """
        Add a stat bar to the unit card.
        
        Args:
            stat_type: The type of stat to add
            value: The stat value (0-20)
            tooltip_text: Tooltip text for the stat
            modification_level: How many tiers this stat has been modified in
        """
        # Constants for positioning stats
        y_offset = 295
        bar_height = 20
        spacing = 3
        
        # Create and add the stat bar
        stat_bar = StatBar(
            manager=self.manager,
            rect=pygame.Rect(
                (10, y_offset + len(self.stat_bars) * (bar_height + spacing)), 
                (280, bar_height)
            ),
            stat_type=stat_type,
            value=value,
            tooltip_text=tooltip_text,
            container=self.card_container,
            modification_level=modification_level
        )
        
        self.stat_bars.append(stat_bar)

    def skip_stat(self, stat_type: StatType):
        """
        Add a stat bar that is grayed out because it doesn't apply to this unit.
        
        Args:
            stat_type: The type of stat
        """
        # Constants for positioning stats
        y_offset = 295
        bar_height = 20
        spacing = 3
        
        # Create the stat bar
        stat_bar = StatBar(
            manager=self.manager,
            rect=pygame.Rect(
                (10, y_offset + len(self.stat_bars) * (bar_height + spacing)), 
                (280, bar_height)
            ),
            container=self.card_container,
            stat_type=stat_type,
            value=0,
            tooltip_text="",
            disabled=True,
            modification_level=0
        )
        
        self.stat_bars.append(stat_bar)
        return stat_bar
    
    def get_window(self):
        """Get the window element for this unit card, or the container if no window."""
        return self.window if self.window is not None else self.card_container
    
    def bring_to_front(self):
        """Bring this unit card to the front with a flash effect."""
        if self.window is not None and self.window.alive():
            # Use pygame-gui's window stack to bring window to front
            window_stack = self.manager.get_window_stack()
            window_stack.move_window_to_front(self.window)
        
        # Start flash animation
        self.start_flash()
    
    def start_flash(self):
        """Start the flash animation effect."""
        if self.window is not None and self.window.alive():
            self.is_flashing = True
            self.flash_time = 0.0
            self.flash_state = False
    
    def _update_flash_theme(self):
        """Update the window theme based on flash state."""
        if self.window is not None and self.window.alive():
            if self.flash_state:
                # Switch to flash theme
                self.window.change_object_id(pygame_gui.core.ObjectID(object_id='#flash_window'))
            else:
                # Switch back to normal theme
                self.window.change_object_id(pygame_gui.core.ObjectID(class_id='window'))
    
    def kill(self):
        """Remove the unit card from the UI."""
        if self.window is not None:
            self.window.kill()
        # Note: If using a container, the container owner is responsible for cleanup
        self.bottom_label.kill()
        self.tips_button.kill()
        self.point_value_label.kill()
        self.point_value_bg.kill()
        if self.faction_label:
            self.faction_label.kill()
        if self.tier_label:
            self.tier_label.kill()
        
    def update(self, time_delta: float):
        """Update all stat bars and animations."""
        # Always update at 30fps
        time_delta = 1/30
        for stat_bar in self.stat_bars:
            stat_bar.update(time_delta)

        # Only show the info mode text if this is a standalone window (not in a panel)
        if self.window is not None:
            if info_mode_manager.info_mode:
                self.bottom_label.set_text(f"Press {info_mode_manager.modifier_key} to close")
            else:
                self.bottom_label.set_text(f"Press {info_mode_manager.modifier_key} to keep open")
        else:
            # When in a panel, leave the bottom label empty
            self.bottom_label.set_text("")
        
        # Update flash animation
        if self.is_flashing:
            self.flash_time += time_delta
            
            # Calculate current alternation
            current_alternation = int(self.flash_time / self.flash_interval)
            new_flash_state = (current_alternation % 2) == 1
            
            # Update theme if state changed
            if new_flash_state != self.flash_state:
                self.flash_state = new_flash_state
                self._update_flash_theme()
            
            # End flash after all alternations
            if self.flash_time >= self.flash_duration:
                self.is_flashing = False
                self.flash_time = 0.0
                self.flash_state = False
                self._update_flash_theme()  # Ensure we end on normal theme
        
        # Update animation
        self.animation_time += time_delta
        
        # Get animation parameters for IDLE
        idle_duration = self.sprite_sheet.animation_durations[AnimationType.IDLE]
        idle_frame_count = self.sprite_sheet.frames[AnimationType.IDLE]
        
        # Loop the animation
        if self.animation_time >= idle_duration:
            self.animation_time = self.animation_time % idle_duration
        
        # Calculate current frame
        frame_duration = idle_duration / idle_frame_count
        new_frame = int(self.animation_time / frame_duration) % idle_frame_count
        
        # Update display if frame changed
        if new_frame != self.current_frame:
            self.current_frame = new_frame
            self.update_unit_display()

    def show_tips(self):
        """Show a glossary entry with tips for this unit at the mouse position."""
        # Import here to avoid circular imports
        from selected_unit_manager import selected_unit_manager
        
        tips_data = self.unit_data.tips
        
        if not tips_data:
            content = "No tips available for this unit."
        else:
            content_lines = []
            
            # Add "Strong when" section
            if "Strong when" in tips_data:
                content_lines.append("Strong when:")
                for tip in tips_data["Strong when"]:
                    content_lines.append(f"  • {tip}")
                content_lines.append("")  # Add blank line
            
            # Add "Weak when" section
            if "Weak when" in tips_data:
                content_lines.append("Weak when:")
                for tip in tips_data["Weak when"]:
                    content_lines.append(f"  • {tip}")
            
            content = '\n'.join(content_lines)
        
        # Use the manager's public method to create the tips entry
        selected_unit_manager.create_tips_glossary_entry(self.name, content)

    def process_event(self, event):
        """Process UI events for the unit card (e.g., Tips button click). Returns True if handled."""
        if event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.tips_button:
            self.show_tips()
            return True
        return False 