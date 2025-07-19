"""UI component for controlling game time speed."""

import pygame
import pygame_gui
from time_manager import time_manager
from events import PLAY_SOUND, PlaySoundEvent, emit_event

class TimeControls:
    """UI component for controlling game time speed."""

    def __init__(
        self,
        manager: pygame_gui.UIManager,
    ) -> None:
        """
        Initialize time control buttons.

        Args:
            manager: The pygame_gui UIManager
        """
        position = (pygame.display.Info().current_w - 250, 10)
        width = 120
        height = 30
        button_width = 30
        label_width = width - (button_width * 3)
        x, y = position

        self.pause_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x, y, button_width, height),
            text="",
            manager=manager,
            object_id=pygame_gui.core.ObjectID(object_id="#pause_button")
        )
        self._update_pause_button_image()

        self.decrease_speed_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + button_width, y, button_width, height),
            text="-",
            manager=manager,
        )

        self.speed_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x + button_width * 2, y, label_width, height),
            text="1",
            manager=manager
        )
        self._update_speed_label()

        self.increase_speed_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + button_width * 2 + label_width, y, button_width, height),
            text="+",
            manager=manager,
        )
        time_manager.enter_battle()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle UI events for the time controls.

        Args:
            event: The pygame event to handle

        Returns:
            True if the event was handled, False otherwise
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.decrease_speed_button:
                time_manager.decrease_game_speed()
                self._update_speed_label()
                return True
            elif event.ui_element == self.increase_speed_button:
                time_manager.increase_game_speed()
                self._update_speed_label()
                return True
            elif event.ui_element == self.pause_button:
                time_manager.toggle_pause()
                self._update_pause_button_image()
                return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                time_manager.toggle_pause()
                self._update_pause_button_image()
                self.pause_button.select()
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
            elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
                time_manager.increase_game_speed()
                self._update_speed_label()
                self.increase_speed_button.select()
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                time_manager.decrease_game_speed()
                self._update_speed_label()
                self.decrease_speed_button.select()
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self.pause_button.unselect()
                return True
            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                self.increase_speed_button.unselect()
                return True
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.decrease_speed_button.unselect()
                return True
        return False

    def _update_speed_label(self) -> None:
        """Update the speed label to show current game speed."""
        speed = time_manager._game_speed
        # Convert fraction to decimal and remove trailing zeros
        speed_str = f"{float(speed):.3f}".rstrip('0').rstrip('.')
        self.speed_label.set_text(speed_str)

    def _update_pause_button_image(self) -> None:
        """Update the pause button image based on the current pause state."""
        if time_manager.dt == 0:
            self.pause_button.change_object_id(pygame_gui.core.ObjectID(object_id="#play_button"))
        else:
            self.pause_button.change_object_id(pygame_gui.core.ObjectID(object_id="#pause_button"))


    def __del__(self):
        time_manager.leave_battle()
