"""Base UI component for count buttons (units and items)."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UIButton, UILabel
from typing import Optional


class BaseCountButton(UIPanel):
    """Base class for UI buttons that display icons with counts."""
    
    size = 80
    
    def __init__(self, 
        x_pos: int,
        y_pos: int,
        count: int,
        interactive: bool,
        manager: pygame_gui.UIManager,
        infinite: bool = False,
        container: Optional[pygame_gui.core.UIContainer] = None,
        hotkey: Optional[str] = None,
    ):
        self.count = count
        self.interactive = interactive
        self.infinite = infinite
        self.manager = manager
        self.hotkey = hotkey
        
        super().__init__(
            relative_rect=pygame.Rect((x_pos, y_pos), (self.size, self.size)),
            manager=manager,
            container=container,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        )
        
        # Create the main button
        self.button = UIButton(
            relative_rect=pygame.Rect((0, 0), (self.size, self.size)),
            text="",  # We'll use an icon instead
            manager=manager,
            container=self,
            object_id=self._get_button_object_id()
        )
        self.button.can_hover = lambda: True
        
        # Create count label
        self.count_label = UILabel(
            relative_rect=pygame.Rect((0, self.size - 25), (self.size, 25)),
            text="inf" if infinite else str(count),
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(class_id="@unit_count_text"),
        )
        
        # Create value label
        self.value_label = UILabel(
            relative_rect=pygame.Rect((0, 0), (self.size, 25)),
            text=str(self._get_point_value()),
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(class_id="@unit_count_text"),
        )
        
        # Create hotkey label if hotkey is provided
        self.hotkey_label = None
        if hotkey:
            self.hotkey_label = UILabel(
                relative_rect=pygame.Rect((0, self.size - 25), (25, 25)),
                text=hotkey,
                manager=manager,
                container=self,
                object_id=pygame_gui.core.ObjectID(class_id="@unit_count_text"),
            )
        
        if not interactive:
            self.button.disable()
    
    def _get_button_object_id(self) -> pygame_gui.core.ObjectID:
        """Get the appropriate object ID for the button. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _get_button_object_id")
    
    def _get_point_value(self) -> int:
        """Get the point value for this item. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _get_point_value")
    
    def update_count(self, count: int) -> None:
        """Update the count without recreating the entire UI element."""
        if self.count == count:
            return
            
        self.count = count
        if self.count_label:
            self.count_label.set_text("inf" if self.infinite else str(count))
    
    def set_interactive(self, interactive: bool) -> None:
        """Update the interactive state without recreating the element."""
        if self.interactive == interactive:
            return
            
        self.interactive = interactive
        if interactive:
            self.button.enable()
        else:
            self.button.disable()

    def set_hotkey(self, hotkey: Optional[str]) -> None:
        """Update the hotkey label without recreating the element."""
        if self.hotkey == hotkey:
            return

        self.hotkey = hotkey
        if hotkey is None:
            if self.hotkey_label is not None:
                self.hotkey_label.kill()
                self.hotkey_label = None
            return

        if self.hotkey_label is None:
            self.hotkey_label = UILabel(
                relative_rect=pygame.Rect((0, self.size - 25), (25, 25)),
                text=hotkey,
                manager=self.manager,
                container=self,
                object_id=pygame_gui.core.ObjectID(class_id="@unit_count_text"),
            )
        else:
            self.hotkey_label.set_text(hotkey)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events for the button. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement handle_event")
