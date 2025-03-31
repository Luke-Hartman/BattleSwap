"""UI component for displaying the congratulations message when all battles are completed."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton, UITextBox
from progress_manager import progress_manager


class CongratulationsPanel(UIPanel):
    """Panel showing congratulations message when all battles are completed."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
    ):
        """Initialize the congratulations panel.
        
        Args:
            manager: The UI manager.
        """
        panel_width = 600
        panel_height = 300
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
            text="Congratulations!",
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )
        
        # Message text
        message_rect = pygame.Rect((20, 110), (panel_width - 40, -1))
        UILabel(
            relative_rect=message_rect,
            text="Thank you for playing Battle Swap, I hope you had fun!",
            manager=manager,
            container=self
        )

        # Corruption information
        corrupted_battles = sum(1 for solution in progress_manager.solutions.values() if solution.solved_corrupted)
        all_battles = len(progress_manager.solutions)
        UILabel(
            relative_rect=pygame.Rect((20, 140), (panel_width - 40, -1)),
            text=f"You completed corrupted versions of {corrupted_battles} out of {all_battles} battles during your campaign!",
            manager=manager,
            container=self
        )
        
        UILabel(
            relative_rect=pygame.Rect((20, 170), (panel_width - 40, -1)),
            text="By continuing to improve your solutions, you can corrupt every battle!",
            manager=manager,
            container=self
        )

        UILabel(
            relative_rect=pygame.Rect((20, 200), (panel_width - 40, -1)),
            text="Please consider leaving feedback through the 'Feedback' button",
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
            progress_manager.mark_congratulations_shown()
            self.kill()
            return True
        return False 