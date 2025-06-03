import pygame
import pygame_gui
from typing import List, Tuple
from ui_components.stat_bar import StatBar
from components.unit_type import UnitType
from entities.units import Faction, get_unit_sprite_sheet
from ui_components.game_data import StatType, UNIT_DATA
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
        self.screen = screen
        self.manager = manager
        self.name = name
        self.stat_bars: List[StatBar] = []
        self.unit_type = unit_type
        
        # Create the window
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(position, (300, 475)),
            window_display_title=f"{name} - {Faction.faction_of(unit_type).name.title()}",
            manager=manager,
            resizable=False
        )
        
        # Create a surface for the unit display area
        unit_display_surface = pygame.Surface((300, 200))
        unit_display_surface.fill(gc.MAP_BATTLEFIELD_COLOR)
        
        # Add the unit display as a UIImage
        self.unit_display = UIImage(
            relative_rect=pygame.Rect((0, 0), (300, 200)),
            image_surface=unit_display_surface,
            manager=manager,
            container=self.window
        )
        
        # Add point value box in upper right corner
        point_value = unit_values.get(unit_type, 0)
        point_value_text = str(point_value)
        
        # Calculate box size based on text
        box_width = 40
        box_height = 25
        
        # Create a background panel for the point value (touching top right corner)
        self.point_value_bg = UIPanel(
            relative_rect=pygame.Rect((300 - box_width, 0), (box_width, box_height)),
            manager=manager,
            container=self.window,
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
        
        # Add description
        full_description = f"{description}"
        
        # Add unit description with clickable links
        self.text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((0, 200), (300, 90)),
            html_text=full_description,
            manager=manager,
            container=self.window
        )
        
        # Store the window reference in the text box's container for link handling
        self.text.ui_container.window = self.window

        # Add bottom row with label and Tips button
        bottom_y = 410
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
        self.sprite_sheet = get_unit_sprite_sheet(unit_type)
        
        # Animation state tracking
        self.animation_time = 0.0
        self.current_frame = 0
        
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
    
    def bring_to_front(self):
        """Bring this unit card to the front, simulating a click behavior."""
        if self.window.alive():
            # Use pygame-gui's built-in bring_to_front method if available
            if hasattr(self.manager, 'bring_to_front'):
                self.manager.bring_to_front(self.window)
            # Fallback: use the window's change_layer method
            elif hasattr(self.window, 'change_layer'):
                # Find the highest layer currently in use and add 1
                current_max = 0
                for element in self.manager.get_root_container().elements:
                    if hasattr(element, '_layer'):
                        current_max = max(current_max, element._layer)
                self.window.change_layer(current_max + 1)
    
    def kill(self):
        """Remove the unit card from the UI."""
        self.window.kill()
        self.bottom_label.kill()
        self.tips_button.kill()
        self.point_value_label.kill()
        self.point_value_bg.kill()
        
    def update(self, time_delta: float):
        """Update all stat bars and animations."""
        # Always update at 60fps
        time_delta = 1/60
        for stat_bar in self.stat_bars:
            stat_bar.update(time_delta)

        if info_mode_manager.info_mode:
            self.bottom_label.set_text(f"Press {info_mode_manager.modifier_key} to close")
        else:
            self.bottom_label.set_text(f"Press {info_mode_manager.modifier_key} to keep open")
        
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
        
        tips_data = UNIT_DATA[self.unit_type].get("tips", {})
        
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
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.tips_button:
            self.show_tips()
            return True
        return False 