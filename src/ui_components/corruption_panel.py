"""UI component for displaying the corruption dialog when battles are corrupted."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton, UITextBox
from keyboard_shortcuts import format_button_text, KeyboardShortcuts
from events import emit_event, PLAY_SOUND, PlaySoundEvent


class CorruptionPanel(UIPanel):
    """Panel showing corruption message when battles are corrupted."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
        corrupted_battles: list[tuple[int, int]],
        world_map_view,
    ):
        """Initialize the corruption panel.
        
        Args:
            manager: The UI manager.
            corrupted_battles: List of corrupted battle coordinates.
            world_map_view: The world map view to get battle names from.
        """
        panel_width = 500
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
            text="Corruption Spreads!",
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )
        
        # Message text with clickable link to corruption glossary entry
        from ui_components.game_data import GlossaryEntryType
        corruption_link = f"<a href='{GlossaryEntryType.CORRUPTION.value}'>corruption</a>"
        message_html = f"The {corruption_link} spreads in reaction to your success..."
        
        message_rect = pygame.Rect((20, 110), (panel_width - 40, 30))
        UITextBox(
            relative_rect=message_rect,
            html_text=message_html,
            manager=manager,
            container=self,
            object_id="@centered_text"
        )

        # Corrupted battles count
        UILabel(
            relative_rect=pygame.Rect((20, 140), (panel_width - 40, -1)),
            text=f"{len(corrupted_battles)} of your claimed hexes have been corrupted!",
            manager=manager,
            container=self
        )
        
        # Instructions
        UILabel(
            relative_rect=pygame.Rect((20, 170), (panel_width - 40, -1)),
            text="You must reclaim these corrupted hexes (marked in red) before continuing to new areas.",
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
            text=format_button_text("Continue", KeyboardShortcuts.SPACE),
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
        # Handle Space key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            # Play UI click sound
            emit_event(PLAY_SOUND, event=PlaySoundEvent(
                filename="ui_click.wav",
                volume=0.5
            ))
            # Simulate clicking the continue button
            pygame.event.post(pygame.event.Event(
                pygame.USEREVENT,
                {'user_type': pygame_gui.UI_BUTTON_PRESSED, 'ui_element': self.continue_button}
            ))
            self.kill()
            return True
            
        if (event.type == pygame_gui.UI_BUTTON_PRESSED and 
            event.ui_element == self.continue_button):
            self.kill()
            return True
        return False 