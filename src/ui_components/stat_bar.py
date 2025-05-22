import pygame
import pygame_gui
from typing import Optional
from ui_components.game_data import StatType

class StatBar:
    """A UI component that displays a named stat with a value from 0-10 as a fill bar."""
    
    # Define colors for each stat type
    STAT_COLORS = {
        StatType.DAMAGE: (200, 50, 50),
        StatType.DURABILITY: (50, 100, 200),
        StatType.SPEED: (200, 200, 50),
        StatType.RANGE: (194, 178, 128),
        StatType.UTILITY: (150, 50, 200)
    }
    
    def __init__(self, 
                 manager: pygame_gui.UIManager, 
                 rect: pygame.Rect, 
                 stat_type: StatType,
                 value: int,
                 tooltip_text: str,
                 container: Optional[pygame_gui.elements.UIPanel] = None,
                 disabled: bool = False):
        """
        Initialize a StatBar component.
        
        Args:
            manager: The UI manager for this component
            rect: Position and size of the component
            stat_type: Type of stat to display
            value: Current value (0-10)
            tooltip_text: Text to display when hovering over the bar
            container: Optional parent container
            disabled: Whether this stat is disabled.
        """
        self.manager = manager
        self.rect = rect
        self.container = container
        self.stat_type = stat_type
        self.name = stat_type.value
        self.value = value
        self.max_value = 10
        self.tooltip_text = tooltip_text
        self.disabled = disabled
        
        # Calculate positions for label and status bar
        label_height = 20
        bar_height = rect.height - label_height
        
        # Create label for the stat name, centered above the bar
        self.label_rect = pygame.Rect(rect.x, rect.y, rect.width, label_height)
        self.label = pygame_gui.elements.UILabel(
            relative_rect=self.label_rect,
            text=self.name,
            manager=manager,
            container=container,
        )
        
        # Create the status bar
        self.status_bar_rect = pygame.Rect(rect.x, rect.y + label_height, rect.width, bar_height)
        self.status_bar = pygame_gui.elements.UIStatusBar(
            relative_rect=self.status_bar_rect,
            manager=manager,
            container=container,
        )
        
        # Set initial value and bar color
        self.status_bar.percent_full = value / self.max_value
        self.status_bar.bar_filled_colour = self.STAT_COLORS[stat_type]
        
        # Set the tooltip if provided and not disabled
        if tooltip_text and not disabled:
            self.status_bar.set_tooltip(tooltip_text, delay=0)
            self.label.set_tooltip(tooltip_text, delay=0)
        
    def update(self, time_delta: float):
        """Update the stat bar components."""
        self.status_bar.update(time_delta)
    
    def set_value(self, value: int):
        """Set a new value for the stat bar and update the visual representation."""
        self.value = min(value, self.max_value)
        self.status_bar.percent_full = self.value / self.max_value
        
    def set_disabled(self, disabled: bool):
        """Set whether this stat bar is disabled (grayed out)."""
        if self.disabled != disabled:
            self.disabled = disabled
            # Update tooltips
            if disabled:
                self.status_bar.set_tooltip(None)
                self.label.set_tooltip(None)
            elif self.tooltip_text:
                self.status_bar.set_tooltip(self.tooltip_text, delay=0)
                self.label.set_tooltip(self.tooltip_text, delay=0)
        
    def kill(self):
        """Remove the stat bar from the UI."""
        self.label.kill()
        self.status_bar.kill() 