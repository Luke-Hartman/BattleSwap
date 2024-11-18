"""Dialog for saving battles in sandbox mode."""
from typing import List, Tuple, Optional
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UITextEntryLine, UIButton, UITextEntryBox
from battles import _save_battles, get_battle, Battle, battles
from components.unit_type import UnitType

class SaveBattleDialog(UIWindow):
    """Dialog window for entering battle details when saving."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        existing_battle_id: Optional[str] = None
    ):
        """Initialize the save battle dialog.
        
        Args:
            manager: The UI manager
            enemy_placements: List of enemy unit placements
            existing_battle_id: Optional existing battle to edit
        """
        window_size = (300, 370)
        window_pos = (
            pygame.display.Info().current_w // 2 - window_size[0] // 2,
            pygame.display.Info().current_h // 2 - window_size[1] // 2
        )
        
        super().__init__(
            rect=pygame.Rect(window_pos, window_size),
            manager=manager,
            window_display_title="Edit Battle" if existing_battle_id else "Save Battle",
            object_id="#save_battle_dialog"
        )
        
        self.enemy_placements = enemy_placements
        self.existing_battle_id = existing_battle_id
        
        # Battle ID input
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 280, 25),
            text="Battle ID:",
            manager=manager,
            container=self
        )
        
        self.battle_id_entry = UITextEntryLine(
            relative_rect=pygame.Rect(10, 40, 280, 30),
            manager=manager,
            container=self,
            initial_text=existing_battle_id if existing_battle_id else ""
        )
        
        # Tips input
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 80, 280, 25),
            text="Tips:",
            manager=manager,
            container=self
        )
        
        initial_tips = '\n'.join(get_battle(existing_battle_id).tip) if existing_battle_id else ""
        self.tip_entry = UITextEntryBox(
            relative_rect=pygame.Rect(10, 110, 280, 180),
            manager=manager,
            container=self,
            initial_text=initial_tips
        )
        
        # Save button
        self.save_button = UIButton(
            relative_rect=pygame.Rect(10, 300, 135, 30),
            text="Save",
            manager=manager,
            container=self
        )
        
        # Cancel button
        self.cancel_button = UIButton(
            relative_rect=pygame.Rect(155, 300, 135, 30),
            text="Cancel",
            manager=manager,
            container=self
        )

    def save_battle(self) -> None:
        """Save the current enemy positions as a new battle."""
        battle_id = self.battle_id_entry.get_text()
        tips_text = self.tip_entry.get_text()
        
        if not battle_id:
            return
        
        # Split tips into lines, removing empty lines
        tips = [line.strip() for line in tips_text.split('\n') if line.strip()]
        if not tips:
            tips = [""]  # Ensure at least one empty tip if none provided
        
        # Find an existing battle if there is one
        try:
            existing_battle = get_battle(battle_id)
        except ValueError:
            existing_battle = None

        # Create new battle data
        new_battle = {
            "id": battle_id,
            "enemies": [
                [unit_type, list(position)]  # Convert position tuple to list for JSON
                for unit_type, position in self.enemy_placements
            ],
            "dependencies": (
                existing_battle.dependencies if existing_battle
                else []
            ),
            "tip": tips
        }
        
        # If the battle already exists replace the battle in its original position
        if existing_battle:
            for i, battle in enumerate(battles):
                if battle.id == self.existing_battle_id:
                    battles[i] = new_battle
                    break
        else:
            # If new battle, append to the end
            battles.append(Battle(**new_battle))
        
        # Save updated battles
        _save_battles()
