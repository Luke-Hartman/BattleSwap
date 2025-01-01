"""Dialog for saving battles."""
import pygame
import pygame_gui
from typing import List, Tuple, Optional, Protocol, Callable
from components.unit_type import UnitType
import battles

class SaveBattleCallback(Protocol):
    """Protocol for save battle callback function."""
    def __call__(self) -> None: ...

class SaveBattleDialog:
    """Dialog for saving battles."""

    def __init__(
        self,
        manager: pygame_gui.UIManager,
        ally_placements: Optional[List[Tuple[UnitType, Tuple[int, int]]]],
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        existing_battle_id: Optional[str],
        hex_coords: Optional[Tuple[int, int]] = None,
        show_battle_button: bool = True,
        show_test_button: bool = True,
    ):
        dialog_width = 300
        dialog_height = 370
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        self.dialog = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(
                (screen_width - dialog_width) // 2,
                (screen_height - dialog_height) // 2,
                dialog_width,
                dialog_height
            ),
            manager=manager,
            window_display_title="Save Battle"
        )

        self.id_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(10, 10, dialog_width - 20, 30),
            manager=manager,
            container=self.dialog,
            initial_text=existing_battle_id if existing_battle_id else ""
        )

        self.tip_entry = pygame_gui.elements.UITextEntryBox(
            relative_rect=pygame.Rect(10, 50, dialog_width - 20, 200),
            manager=manager,
            container=self.dialog,
            initial_text="\n".join(battles.get_battle_id(existing_battle_id).tip) if existing_battle_id else "TODO"
        )

        # Calculate button layout based on which buttons to show
        visible_button_count = sum([show_battle_button, show_test_button, True])  # +1 for cancel
        button_width = (dialog_width - (visible_button_count + 1) * 10) // visible_button_count
        current_x = 10

        self.save_battle_button = None
        self.save_test_button = None
        
        if show_battle_button:
            self.save_battle_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, 300, button_width, 30),
                text='Save Battle',
                manager=manager,
                container=self.dialog
            )
            current_x += button_width + 10

        if show_test_button:
            self.save_test_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, 300, button_width, 30),
                text='Save Test',
                manager=manager,
                container=self.dialog
            )
            current_x += button_width + 10

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, 300, button_width, 30),
            text='Cancel',
            manager=manager,
            container=self.dialog
        )

        self.enemy_placements = enemy_placements
        self.ally_placements = ally_placements
        self.existing_battle_id = existing_battle_id
        self.hex_coords = (hex_coords if hex_coords is not None else 
                          (battles.get_battle_id(existing_battle_id).hex_coords 
                           if existing_battle_id else None))

    def save_battle(self, is_test: bool) -> None:
        """Save the battle with the current settings."""
        battle_id = self.id_entry.get_text()
        tip = self.tip_entry.get_text().split('\n') if self.tip_entry.get_text() else ["TODO"]

        battle = battles.Battle(
            id=battle_id,
            enemies=self.enemy_placements,
            allies=self.ally_placements if is_test else None,
            tip=tip,
            dependencies=[],
            is_test=is_test,
            hex_coords=self.hex_coords if not is_test else None
        )

        if self.existing_battle_id:
            # Always use update_battle when editing an existing battle
            battles.update_battle(battles.get_battle_id(self.existing_battle_id), battle)
        else:
            # Only use add_battle for completely new battles
            battles.add_battle(battle)

    def kill(self) -> None:
        """Remove the dialog."""
        self.dialog.kill()