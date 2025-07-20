import pygame
import pygame_gui
from typing import Optional
from ui_components.game_data import StatType

class StatBar:
    """A UI component that displays a named stat with a value from 0-20 as segmented bars with text titles."""
    
    # Define colors for each stat type
    STAT_COLORS = {
        StatType.DAMAGE: (200, 50, 50),
        StatType.DEFENSE: (50, 100, 200),
        StatType.SPEED: (200, 200, 50),
        StatType.RANGE: (194, 178, 128),
        StatType.UTILITY: (170, 0, 255)
    }
    
    # Text titles for each stat type
    STAT_TITLES = {
        StatType.DAMAGE: "Damage",
        StatType.DEFENSE: "Defense", 
        StatType.SPEED: "Speed",
        StatType.RANGE: "Range",
        StatType.UTILITY: "Utility"
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
                 disabled: bool = False,
                 modification_level: int = 0):
        """
        Initialize a StatBar component.
        
        Args:
            manager: The UI manager for this component
            rect: Position and size of the component
            stat_type: Type of stat to display
            value: Current value (0-20)
            tooltip_text: Text to display when hovering over the bar
            container: Optional parent container
            disabled: Whether this stat is disabled
            modification_level: How many tiers this stat has been modified in (0=none, 1=one tier, 2=two tiers)
        """
        self.manager = manager
        self.rect = rect
        self.container = container
        self.stat_type = stat_type
        self.name = stat_type.value
        self.value = value
        self.max_value = 20
        self.tooltip_text = tooltip_text if not disabled else "N/A"
        self.disabled = disabled
        self.modification_level = modification_level
        
        # Text title size and spacing
        self.title_width = 75
        self.title_spacing = 10
        
        # Create text title element
        title_rect = pygame.Rect(
            rect.x, 
            rect.y + (rect.height - 20) // 2,  # Center vertically
            self.title_width,
            20
        )
        
        # Add modification indicators to title based on modification level
        title_text = self.STAT_TITLES[stat_type]
        if self.modification_level > 0:
            # Add appropriate number of plus signs
            pluses = "+" * self.modification_level
            title_text += pluses
            
        self.title_element = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=manager,
            container=container,
            object_id=pygame_gui.core.ObjectID(object_id='@right_aligned_text')
        )
        
        # Set tooltip on title if not disabled
        self.title_element.set_tooltip(self.tooltip_text, delay=0)
        
        # Calculate bar area - make it narrower and move it right to maintain same right edge
        self.bar_rect = pygame.Rect(
            rect.x + self.title_width + self.title_spacing,
            rect.y,
            rect.width - self.title_width - self.title_spacing,
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
        
        # Calculate segments to fill with quarter precision
        # We have 5 segments, values 0-20
        # Each segment represents 4 values, with quarter increments
        # Values 0-20 map to 0-5 segments with quarter precision
        
        if self.value == 0:
            filled_segments = 0.0
        else:
            # Map values 1-20 to quarter increments
            # Value 1 = 0.25, Value 2 = 0.5, Value 3 = 0.75, Value 4 = 1.0, etc.
            filled_segments = self.value / 4.0
        
        # Calculate full segments and fractional part
        full_segments = int(filled_segments)
        fraction = filled_segments - full_segments
        
        # Round fraction to nearest quarter (0, 0.25, 0.5, 0.75, 1.0)
        quarter_level = round(fraction * 4) / 4
        
        # Get the stat color
        stat_color = self.STAT_COLORS[self.stat_type]
        
        # Colors for filled and unfilled segments
        if self.disabled:
            fill_color = tuple(int(c * 0.4) for c in stat_color)
        else:
            fill_color = stat_color
            # Make modified stats slightly brighter
            if self.modification_level > 0:
                fill_color = tuple(min(255, int(c * 1.2)) for c in stat_color)
        
        # Unfilled segment color (dark gray)
        unfilled_color = (60, 60, 60)
        
        # Draw each segment
        for i in range(self.NUM_SEGMENTS):
            segment_x = i * (self.segment_width + self.segment_gap)
            segment_rect = pygame.Rect(segment_x, 0, self.segment_width, self.segment_height)
            
            if i < full_segments:
                # Fully filled segment
                pygame.draw.rect(self.segments_surface, fill_color, segment_rect)
                # Add a subtle border for modified stats
                if self.modification_level > 0:
                    pygame.draw.rect(self.segments_surface, (255, 255, 255), segment_rect, 1)
            elif i == full_segments and quarter_level > 0:
                # Partially filled segment
                # Draw the unfilled background first
                pygame.draw.rect(self.segments_surface, unfilled_color, segment_rect)
                
                # Calculate the width of the filled portion based on quarter level
                if quarter_level >= 1.0:
                    # Full segment (shouldn't happen here, but handle it)
                    fill_width = self.segment_width
                else:
                    # Quarter level: 0.25 = 1/4, 0.5 = 1/2, 0.75 = 3/4
                    fill_width = int(self.segment_width * quarter_level)
                
                # Draw the filled portion
                if fill_width > 0:
                    fill_rect = pygame.Rect(segment_x, 0, fill_width, self.segment_height)
                    pygame.draw.rect(self.segments_surface, fill_color, fill_rect)
                    # Add border for modified stats
                    if self.modification_level > 0:
                        pygame.draw.rect(self.segments_surface, (255, 255, 255), fill_rect, 1)
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
        self.title_element.kill()
        self.segments_element.kill() 