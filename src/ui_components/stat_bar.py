import pygame
import pygame_gui
from typing import Optional
from ui_components.game_data import StatType

class StatBar:
    """A UI component that displays a named stat with a value from 0-10 as segmented bars with icons."""
    
    # Define colors for each stat type
    STAT_COLORS = {
        StatType.DAMAGE: (200, 50, 50),
        StatType.DEFENSE: (50, 100, 200),
        StatType.SPEED: (200, 200, 50),
        StatType.RANGE: (194, 178, 128),
        StatType.UTILITY: (150, 50, 200)
    }
    
    # Icon paths for each stat type
    STAT_ICONS = {
        StatType.DAMAGE: "assets/icons/DamageIcon.png",
        StatType.DEFENSE: "assets/icons/DefenseIcon.png",
        StatType.SPEED: "assets/icons/SpeedIcon.png",
        StatType.RANGE: "assets/icons/RangeIcon.png",
        StatType.UTILITY: "assets/icons/UtilityIcon.png"
    }
    
    # Number of segments to display
    NUM_SEGMENTS = 5
    
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
        self.tooltip_text = f"{stat_type.value.title()}: {tooltip_text}" if not disabled else f"{stat_type.value.title()}: N/A"
        self.disabled = disabled
        
        # Icon size and spacing
        self.icon_size = rect.height
        self.icon_spacing = 10
        
        # Load and scale the icon
        icon_path = self.STAT_ICONS[stat_type]
        self.icon_surface = pygame.image.load(icon_path)
        self.icon_surface = pygame.transform.scale(self.icon_surface, (self.icon_size, self.icon_size))
        
        # Create icon UI element
        icon_rect = pygame.Rect(
            rect.x, 
            rect.y + (rect.height - self.icon_size) // 2,  # Center vertically
            self.icon_size,
            self.icon_size
        )
        self.icon_element = pygame_gui.elements.UIImage(
            relative_rect=icon_rect,
            image_surface=self.icon_surface,
            manager=manager,
            container=container
        )
        
        # Set tooltip on icon if not disabled
        self.icon_element.set_tooltip(self.tooltip_text, delay=0)
        
        # Calculate bar area
        self.bar_rect = pygame.Rect(
            rect.x + self.icon_size + self.icon_spacing,
            rect.y,
            rect.width - self.icon_size - self.icon_spacing,
            rect.height
        )
        
        # Calculate segment dimensions
        self.segment_gap = 2
        self.segment_width = (self.bar_rect.width - (self.NUM_SEGMENTS - 1) * self.segment_gap) // self.NUM_SEGMENTS
        self.segment_height = self.bar_rect.height
        
        # Create surface for drawing segments
        self.segments_surface = pygame.Surface((self.bar_rect.width, self.bar_rect.height), pygame.SRCALPHA)
        self._update_segments()
        
        # Create a UIImage element for the segments
        self.segments_element = pygame_gui.elements.UIImage(
            relative_rect=self.bar_rect,
            image_surface=self.segments_surface,
            manager=manager,
            container=container
        )
        self.segments_element.set_tooltip(self.tooltip_text, delay=0)
    
    def _update_segments(self):
        """Update the visual state of segments based on current value."""
        # Clear the surface
        self.segments_surface.fill((0, 0, 0, 0))
        
        # Calculate segments to fill
        # We have 5 segments, values 0-10
        # Each segment represents 2 values
        # But we want any non-zero value to show at least half a segment
        
        if self.value == 0:
            # Nothing filled
            filled_segments = 0.0
        elif self.value == 1:
            # Special case: show half a segment for value 1
            filled_segments = 0.5
        else:
            # Values 2-10 map linearly: 2->1, 3->1.5, 4->2, ..., 10->5
            filled_segments = self.value / 2.0
        
        # Convert to full and half segments
        full_segments = int(filled_segments)
        has_half = (filled_segments - full_segments) >= 0.5
        if full_segments == 0 and self.value > 0:
            has_half = True
        
        # Get the stat color
        stat_color = self.STAT_COLORS[self.stat_type]
        
        # Colors for filled and unfilled segments
        if self.disabled:
            fill_color = tuple(int(c * 0.4) for c in stat_color)
        else:
            fill_color = stat_color
        
        # Unfilled segment color (dark gray)
        unfilled_color = (60, 60, 60)
        
        # Draw each segment
        for i in range(self.NUM_SEGMENTS):
            segment_x = i * (self.segment_width + self.segment_gap)
            segment_rect = pygame.Rect(segment_x, 0, self.segment_width, self.segment_height)
            
            if i < full_segments:
                # Fully filled segment
                pygame.draw.rect(self.segments_surface, fill_color, segment_rect)
            elif i == full_segments and has_half:
                # Half-filled segment
                # Draw the unfilled background first
                pygame.draw.rect(self.segments_surface, unfilled_color, segment_rect)
                # Then draw the half-filled portion on top
                half_rect = pygame.Rect(segment_x, 0, self.segment_width // 2, self.segment_height)
                pygame.draw.rect(self.segments_surface, fill_color, half_rect)
            else:
                # Unfilled segment
                pygame.draw.rect(self.segments_surface, unfilled_color, segment_rect)
        
        # Update the UIImage with the new surface
        if hasattr(self, 'segments_element'):
            self.segments_element.set_image(self.segments_surface)
    
    def update(self, time_delta: float):
        """Update the stat bar components."""
        # pygame_gui elements update themselves
        pass
    
    def set_value(self, value: int):
        """Set a new value for the stat bar and update the visual representation."""
        self.value = min(value, self.max_value)
        self._update_segments()
        
    def kill(self):
        """Remove the stat bar from the UI."""
        self.icon_element.kill()
        self.segments_element.kill() 