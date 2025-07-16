"""UI component for displaying the upgrade tutorial when users first unlock upgrade points."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton


class UpgradeTutorialPanel(UIPanel):
    """Panel explaining the upgrade system when users first unlock upgrade points."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
    ):
        """Initialize the upgrade tutorial panel.
        
        Args:
            manager: The UI manager.
        """
        panel_width = 370
        panel_height = 130
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        super().__init__(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=manager
        )
        
        # Simple message
        UILabel(
            relative_rect=pygame.Rect((20, 20), (panel_width - 40, 50)),
            text="You can now upgrade units!",
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(
                object_id="#upgrade_tutorial_text"
            )
        )
        
        # OK button
        button_width = 100
        button_height = 30
        button_x = (panel_width - button_width) // 2
        button_y = panel_height - button_height - 15
        
        self.ok_button = UIButton(
            relative_rect=pygame.Rect((button_x, button_y), (button_width, button_height)),
            text="Got it!",
            manager=manager,
            container=self
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle button click events.
        
        Args:
            event: The pygame event to handle.
            
        Returns:
            True if the event was handled, False otherwise.
        """
        if (event.type == pygame.USEREVENT and 
            event.user_type == pygame_gui.UI_BUTTON_PRESSED and 
            event.ui_element == self.ok_button):
            self.kill()
            return True
        return False 