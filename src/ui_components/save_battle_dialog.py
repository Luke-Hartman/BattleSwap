"""Dialog for saving battles in sandbox mode."""
import json
from pathlib import Path
from typing import List, Tuple, Callable
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UITextEntryLine, UIButton, UITextEntryBox
from battles import reload_battles
from components.unit_type import UnitType

class SaveBattleDialog(UIWindow):
    """Dialog window for entering battle details when saving."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        on_complete: Callable[[], None]
    ):
        """Initialize the save battle dialog."""
        window_size = (300, 370)
        window_pos = (
            pygame.display.Info().current_w // 2 - window_size[0] // 2,
            pygame.display.Info().current_h // 2 - window_size[1] // 2
        )
        
        super().__init__(
            rect=pygame.Rect(window_pos, window_size),
            manager=manager,
            window_display_title="Save Battle",
            object_id="#save_battle_dialog"
        )
        
        self.enemy_placements = enemy_placements
        self.on_complete = on_complete
        
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
            container=self
        )
        
        # Tips input
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 80, 280, 25),
            text="Tips:",
            manager=manager,
            container=self
        )
        
        self.tip_entry = UITextEntryBox(
            relative_rect=pygame.Rect(10, 110, 280, 180),
            manager=manager,
            container=self,
            initial_text=""
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
        
        # Create new battle data
        new_battle = {
            "id": battle_id,
            "enemies": [
                [unit_type, list(position)]  # Convert position tuple to list for JSON
                for unit_type, position in self.enemy_placements
            ],
            "dependencies": [],  # New battles start with no dependencies
            "tip": tips
        }
        
        # Load existing battles
        battles_path = Path(__file__).parent.parent.parent / 'data' / 'battles.json'
        with open(battles_path, 'r') as f:
            battles_data = json.load(f)
        
        # Update or add new battle
        for i, battle in enumerate(battles_data):
            if battle["id"] == battle_id:
                battles_data[i] = new_battle
                break
        else:
            battles_data.append(new_battle)
        
        # Save updated battles
        with open(battles_path, 'w') as f:
            json.dump(battles_data, f, indent=2)
        reload_battles()
