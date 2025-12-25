"""UI component for controlling game time speed."""

import pygame
import pygame_gui
import timing
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from keyboard_shortcuts import format_button_text, KeyboardShortcuts
from settings import settings, save_settings

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
        height = 30
        button_width = 30
        button_spacing = 5
        x, y = position

        self.pause_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x, y, button_width, height),
            text="",
            manager=manager,
            object_id=pygame_gui.core.ObjectID(object_id="#pause_button")
        )
        self.pause_button.tool_tip_text = format_button_text("Pause/Play", KeyboardShortcuts.SPACE)
        self.pause_button.tool_tip_delay = 0
        self._update_pause_button_image()

        self.fast_forward_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + button_width + button_spacing, y, button_width, height),
            text=">>",
            manager=manager,
        )
        self.fast_forward_button.tool_tip_text = format_button_text("Fast Forward", KeyboardShortcuts.SHIFT)
        self.fast_forward_button.tool_tip_delay = 0
        # Load fast-forward enabled state from settings
        self._fast_forward_enabled = settings.FAST_FORWARD_ENABLED if settings else False
        
        checkbox_width = 60
        checkbox_spacing = 5
        self.toggle_mode_checkbox = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                x + button_width + button_spacing + button_width + checkbox_spacing,
                y,
                checkbox_width,
                height
            ),
            text="Hold",
            manager=manager,
        )
        self.toggle_mode_checkbox.tool_tip_text = "Toggle or Hold to Fast Forward"
        self.toggle_mode_checkbox.tool_tip_delay = 0
        # Load toggle mode setting from settings
        self._toggle_mode_enabled = settings.TOGGLE_FAST_FORWARD if settings else False
        
        # Check if shift is currently held
        keys = pygame.key.get_pressed()
        shift_held_now = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self._shift_held = shift_held_now
        
        # If toggle mode is enabled, we shouldn't use shift_held state
        if self._toggle_mode_enabled:
            self._shift_held = False
        
        # Initialize game speed based on current state
        self._update_game_speed()
        self._update_fast_forward_button_appearance()
        # Initialize checkbox text
        self._update_toggle_mode_button_text()
        timing.enter_battle()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle UI events for the time controls.

        Args:
            event: The pygame event to handle

        Returns:
            True if the event was handled, False otherwise
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.fast_forward_button:
                self._fast_forward_enabled = not self._fast_forward_enabled
                # Save the setting
                if settings:
                    settings.FAST_FORWARD_ENABLED = self._fast_forward_enabled
                    save_settings()
                self._update_game_speed()
                self._update_fast_forward_button_appearance()
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
            elif event.ui_element == self.pause_button:
                timing.toggle_pause()
                self._update_pause_button_image()
                return True
            elif event.ui_element == self.toggle_mode_checkbox:
                old_toggle_mode = self._toggle_mode_enabled
                self._toggle_mode_enabled = not self._toggle_mode_enabled
                
                # Reset fast-forward to off when mode switches
                self._fast_forward_enabled = False
                if settings:
                    settings.FAST_FORWARD_ENABLED = False
                
                # Save the toggle mode setting
                if settings:
                    settings.TOGGLE_FAST_FORWARD = self._toggle_mode_enabled
                    save_settings()
                
                # Clear shift held since mode has changed
                self._shift_held = False
                
                # Update checkbox text
                self._update_toggle_mode_button_text()
                
                self._update_game_speed()
                self._update_fast_forward_button_appearance()
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                timing.toggle_pause()
                self._update_pause_button_image()
                self.pause_button.select()
                emit_event(PLAY_SOUND, event=PlaySoundEvent(
                    filename="ui_click.wav",
                    volume=0.5
                ))
                return True
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                if self._toggle_mode_enabled:
                    # In toggle mode, shift toggles fast-forward on/off
                    self._fast_forward_enabled = not self._fast_forward_enabled
                    # Save the setting
                    if settings:
                        settings.FAST_FORWARD_ENABLED = self._fast_forward_enabled
                        save_settings()
                    self._update_game_speed()
                    self._update_fast_forward_button_appearance()
                    emit_event(PLAY_SOUND, event=PlaySoundEvent(
                        filename="ui_click.wav",
                        volume=0.5
                    ))
                else:
                    # In hold mode, shift activates fast-forward while held
                    self._shift_held = True
                    self._update_game_speed()
                    self._update_fast_forward_button_appearance()
                return True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self.pause_button.unselect()
                return True
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                if not self._toggle_mode_enabled:
                    # Only release shift hold when not in toggle mode
                    self._shift_held = False
                    self._update_game_speed()
                    self._update_fast_forward_button_appearance()
                return True
        
        # Check shift key state continuously (for when shift is held when component is created)
        # Only relevant when not in toggle mode
        if not self._toggle_mode_enabled:
            keys = pygame.key.get_pressed()
            shift_held_now = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            if shift_held_now != self._shift_held:
                self._shift_held = shift_held_now
                self._update_game_speed()
                self._update_fast_forward_button_appearance()
        
        return False
    
    def _update_game_speed(self) -> None:
        """Update the game speed based on button state and shift key."""
        if self._toggle_mode_enabled:
            # In toggle mode, only use button toggle state
            if self._fast_forward_enabled:
                timing.set_game_speed_4x()
            else:
                timing.set_game_speed_1x()
        else:
            # In hold mode, use shift held or button toggle state
            if self._shift_held or self._fast_forward_enabled:
                timing.set_game_speed_4x()
            else:
                timing.set_game_speed_1x()
    
    def _update_fast_forward_button_appearance(self) -> None:
        """Update the fast forward button appearance based on state."""
        if self._toggle_mode_enabled:
            # In toggle mode, only show pressed when button is toggled
            if self._fast_forward_enabled:
                self.fast_forward_button.select()
            else:
                self.fast_forward_button.unselect()
        else:
            # In hold mode, show pressed when button is toggled or shift is held
            if self._fast_forward_enabled or self._shift_held:
                self.fast_forward_button.select()
            else:
                self.fast_forward_button.unselect()
    
    def _update_toggle_mode_button_text(self) -> None:
        """Update the toggle mode button text to reflect current state."""
        if self._toggle_mode_enabled:
            self.toggle_mode_checkbox.set_text("Toggle")
        else:
            self.toggle_mode_checkbox.set_text("Hold")

    def _update_pause_button_image(self) -> None:
        """Update the pause button image based on the current pause state."""
        if timing.get_dt() == 0:
            self.pause_button.change_object_id(pygame_gui.core.ObjectID(object_id="#play_button"))
        else:
            self.pause_button.change_object_id(pygame_gui.core.ObjectID(object_id="#pause_button"))
        self.pause_button.tool_tip_delay = 0


    def __del__(self):
        timing.leave_battle()
