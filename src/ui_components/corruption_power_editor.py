"""UI component for editing corruption powers in the battle setup scene."""

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton, UIDropDownMenu, UISelectionList, UITextEntryLine
from typing import List, Callable
from corruption_powers import CorruptionPower, IncreasedMaxHealth, IncreasedDamage, IncreasedMovementSpeed, IncreasedAttackSpeed
from components.team import TeamType

class CorruptionPowerEditorDialog(UIPanel):
    """Dialog for editing corruption powers of a battle."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
        current_powers: List[CorruptionPower],
        on_save: Callable[[List[CorruptionPower]], None],
    ):
        """Initialize the corruption power editor dialog.
        
        Args:
            manager: The UI manager
            current_powers: List of current corruption powers
            on_save: Callback function called when powers are saved
        """
        panel_width = 600
        panel_height = 550
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        super().__init__(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=manager
        )
        
        # Store the manager for later use
        self.manager = manager
        self.current_powers = current_powers.copy() if current_powers else []
        self.on_save = on_save
        
        # Title
        UILabel(
            relative_rect=pygame.Rect((0, 30), (panel_width, 70)),
            text="Edit Corruption Powers",
            manager=manager,
            container=self,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )
        
        # Get power descriptions as plain strings
        power_descriptions = []
        for power in self.current_powers:
            power_descriptions.append(power.description)
        
        # Create the selection list with string items, not tuples
        self.powers_list = UISelectionList(
            relative_rect=pygame.Rect((20, 100), (panel_width - 40, 200)),
            item_list=power_descriptions,  # Use the explicit string list we created
            manager=manager,
            container=self,
            allow_multi_select=True
        )
        
        # Add new power section
        y_offset = 320
        
        # Power type dropdown
        UILabel(
            relative_rect=pygame.Rect((20, y_offset - 25), (200, 20)),
            text="Power Type:",
            manager=manager,
            container=self
        )
        self.power_type_dropdown = UIDropDownMenu(
            relative_rect=pygame.Rect((20, y_offset), (200, 30)),
            options_list=[
                "increased_max_health",
                "increased_damage",
                "increased_movement_speed",
                "increased_attack_speed"
            ],
            starting_option="increased_max_health",
            manager=manager,
            container=self
        )
        
        # Team dropdown
        UILabel(
            relative_rect=pygame.Rect((240, y_offset - 25), (200, 20)),
            text="Apply to Team:",
            manager=manager,
            container=self
        )
        self.team_dropdown = UIDropDownMenu(
            relative_rect=pygame.Rect((240, y_offset), (200, 30)),
            options_list=["None", "Player", "Enemy"],
            starting_option="Enemy",
            manager=manager,
            container=self
        )
        
        # Increase percent entry
        UILabel(
            relative_rect=pygame.Rect((20, y_offset + 45), (100, 30)),
            text="Increase %:",
            manager=manager,
            container=self
        )
        self.increase_percent_entry = UITextEntryLine(
            relative_rect=pygame.Rect((130, y_offset + 45), (100, 30)),
            manager=manager,
            container=self
        )
        self.increase_percent_entry.set_text("100")
        
        # Add power button
        self.add_power_button = UIButton(
            relative_rect=pygame.Rect((20, y_offset + 90), (200, 30)),
            text="Add Power",
            manager=manager,
            container=self
        )
        
        # Remove selected power button
        self.remove_power_button = UIButton(
            relative_rect=pygame.Rect((240, y_offset + 90), (200, 30)),
            text="Remove Selected",
            manager=manager,
            container=self
        )
        
        # Save button
        self.save_button = UIButton(
            relative_rect=pygame.Rect((panel_width - 220, panel_height - 60), (200, 30)),
            text="Save Changes",
            manager=manager,
            container=self
        )
        
    def process_event(self, event: pygame.event.Event) -> bool:
        """Process a pygame event.
        
        Returns:
            bool: True if the event was consumed, False otherwise
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_power_button:
                self._add_power()
                return True
            elif event.ui_element == self.remove_power_button:
                self._remove_selected_power()
                return True
            elif event.ui_element == self.save_button:
                self._save_changes()
                return True

    def _add_power(self) -> None:
        """Add a new corruption power based on the current UI state."""
        try:
            increase_percent = float(self.increase_percent_entry.get_text())
        except ValueError:
            return
            
        team_str = self.team_dropdown.selected_option[0]
        team = None
        if team_str == "Player":
            team = TeamType.TEAM1
        elif team_str == "Enemy":
            team = TeamType.TEAM2
        elif team_str == "None":
            team = None
        else:
            raise ValueError(f"Invalid team: {team_str}")
        # Create new power based on selected type
        power = None
        power_type = self.power_type_dropdown.selected_option[0]
        if power_type == "increased_max_health":
            power = IncreasedMaxHealth(required_team=team, increase_percent=increase_percent)
        elif power_type == "increased_damage":
            power = IncreasedDamage(required_team=team, increase_percent=increase_percent)
        elif power_type == "increased_movement_speed":
            power = IncreasedMovementSpeed(required_team=team, increase_percent=increase_percent)
        elif power_type == "increased_attack_speed":
            power = IncreasedAttackSpeed(required_team=team, increase_percent=increase_percent)
        else:
            raise NotImplementedError(f"Power type {power_type} not implemented")
        
        if power is not None:
            self.current_powers.append(power)
            power_descriptions = [p.description for p in self.current_powers]
            self.powers_list.kill()
            self.powers_list = UISelectionList(
                relative_rect=pygame.Rect((20, 100), (self.rect.width - 40, 200)),
                item_list=power_descriptions,
                manager=self.manager,
                container=self,
                allow_multi_select=True
            )
        
    def _remove_selected_power(self) -> None:
        """Remove the currently selected corruption power."""
        selected_items = self.powers_list.get_multi_selection()
        if not selected_items:
            return

        # Create a new list without the selected powers
        new_powers = []
        for power in self.current_powers:
            # Check if this power's description matches any selected item's text
            # Selected items might be tuples (text, object_id) or just strings
            should_keep = True
            for item in selected_items:
                if isinstance(item, tuple) and item[0] == power.description:
                    should_keep = False
                    break
                elif item == power.description:
                    should_keep = False
                    break
            
            if should_keep:
                new_powers.append(power)
        
        # Update our data list
        self.current_powers = new_powers
        
        # First kill the current list
        self.powers_list.kill()
        
        # Then create a new one with the updated data
        power_descriptions = [p.description for p in self.current_powers]
        
        self.powers_list = UISelectionList(
            relative_rect=pygame.Rect((20, 100), (self.rect.width - 40, 200)),
            item_list=power_descriptions,
            manager=self.manager,
            container=self,
            allow_multi_select=True
        )
        
    def _save_changes(self) -> None:
        """Save the current corruption powers and close the dialog."""
        self.on_save(self.current_powers)
        self.kill()