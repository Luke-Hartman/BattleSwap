"""UI component for displaying the special congratulations message when all battles are corrupted and beaten."""


import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton
from progress_manager import progress_manager


class CorruptionCongratulationsPanel(UIPanel):
    """Panel showing special congratulations message when all battles are corrupted and beaten."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
    ):
        """Initialize the corruption master panel.
        
        Args:
            manager: The UI manager.
        """
        panel_width = 600
        panel_height = 330
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        super().__init__(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=manager
        )
        
        # Title
        UILabel(
            relative_rect=pygame.Rect((0, 20), (panel_width, 70)),
            text="Battle Swap Master!",
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )
        
        # Main message
        UILabel(
            relative_rect=pygame.Rect((20, 110), (panel_width - 40, -1)),
            text="Wow, you corrupted and beat every battle!!",
            manager=manager,
            container=self
        )

        # Achievement message
        UILabel(
            relative_rect=pygame.Rect((20, 140), (panel_width - 40, -1)),
            text="This is very impressive, and not something many others have done.",
            manager=manager,
            container=self
        )
        
        # Feedback request
        UILabel(
            relative_rect=pygame.Rect((20, 170), (panel_width - 40, -1)),
            text="I would be very interested in your feedback, especially on the corruption system.",
            manager=manager,
            container=self
        )
        
        # Specific questions
        UILabel(
            relative_rect=pygame.Rect((20, 200), (panel_width - 40, -1)),
            text="Is the corruption system too easy or hard? Is it fun or stressful?",
            manager=manager,
            container=self
        )
        
        UILabel(
            relative_rect=pygame.Rect((20, 230), (panel_width - 40, -1)),
            text="How well do you think you understand how it works, and does that matter to you?",
            manager=manager,
            container=self
        )
        
        # Continue button
        button_width = 150
        button_height = 40
        button_y = panel_height - button_height - 20
        
        self.continue_button = UIButton(
            relative_rect=pygame.Rect(
                ((panel_width - button_width) // 2, button_y),
                (button_width, button_height)
            ),
            text="Continue Playing",
            manager=manager,
            container=self
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events.
        
        Args:
            event: The pygame event to handle.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if (event.type == pygame_gui.UI_BUTTON_PRESSED and 
            event.ui_element == self.continue_button):
            progress_manager.mark_corruption_congratulations_shown()
            self.kill()
            return True
        return False