"""UI component for displaying progress information."""

from typing import Optional, Dict
import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel
from pygame_gui.core import ObjectID

import battles
from progress_manager import calculate_points_for_units, progress_manager
from components.team import TeamType
from scene_utils import get_unit_placements
from game_constants import gc

class ProgressPanel(UIPanel):
    """Panel showing progress information including battle points, completion stats, and barracks info."""
    
    def __init__(
        self,
        relative_rect: pygame.Rect,
        manager: pygame_gui.UIManager,
        current_battle: Optional[battles.Battle] = None,
        container: Optional[pygame_gui.core.UIContainer] = None,
        is_setup_mode: bool = False,
    ):
        super().__init__(
            relative_rect=relative_rect,
            manager=manager,
            container=container,
            object_id='#progress_panel'
        )
        
        # Store manager for later use
        self.manager = manager
        
        # Layout constants
        self.y_offset = 10
        self.label_height = 20
        self.label_spacing = 0
        self.side_margin = 15
        
        # Create the UI elements
        self.is_setup_mode = is_setup_mode
        self.create_ui_elements(current_battle)

    def create_ui_elements(self, current_battle: Optional[battles.Battle]) -> None:
        """Create all UI elements with the current battle information."""
        y_offset = self.y_offset
        
        # Battle points information
        if current_battle:
            if self.is_setup_mode:
                # In setup mode, use currently deployed units
                current_units = get_unit_placements(TeamType.TEAM1, current_battle)
                player_points = calculate_points_for_units(current_units)
                enemy_points = calculate_points_for_units(current_battle.enemies or [])
            elif current_battle.hex_coords in progress_manager.solutions:
                # In normal mode, use saved solution
                player_points = calculate_points_for_units(current_battle.allies or [])
                enemy_points = calculate_points_for_units(current_battle.enemies or [])
            elif current_battle.hex_coords in progress_manager.available_battles():
                player_points = "-"
                enemy_points = calculate_points_for_units(current_battle.enemies or [])
        else:
            player_points = "-"
            enemy_points = "-"
            
        # Battle points row
        self.battle_points_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"{player_points} pts vs {enemy_points} pts",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        y_offset += self.label_height + self.label_spacing

        # Barracks info
        barracks_units = []
        for unit_type, count in progress_manager.available_units(current_battle=current_battle).items():
            barracks_units.extend([(unit_type, (0, 0))] * count)
        barracks_points = calculate_points_for_units(barracks_units)
        
        self.barracks_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"{barracks_points} pts unused",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        y_offset += self.label_height + self.label_spacing

        # Corruption info
        corruption_threshold = gc.CORRUPTION_TRIGGER_POINTS
        self.corruption_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"({corruption_threshold} pts unused corrupts)",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        y_offset += self.label_height + self.label_spacing

        # Campaign completion stats
        denominator = 2 * len([b for b in battles.get_battles() if not b.is_test])
        numerator = 0
        for solution in progress_manager.solutions.values():
            if solution.solved_corrupted:
                numerator += 2
            else:
                numerator += 1
        percentage = int(numerator / denominator * 100)
        
        # Total battles
        self.progress_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"{percentage}% completion",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        y_offset += self.label_height + self.label_spacing

    def kill_ui_elements(self) -> None:
        """Kill all UI elements."""
        self.battle_points_label.kill()
        self.progress_label.kill()
        self.barracks_label.kill()
        self.corruption_label.kill()

    def update_battle(self, new_battle: Optional[battles.Battle]) -> None:
        """Update the displayed battle information."""
        # Kill all existing UI elements
        self.kill_ui_elements()
        
        # Recreate UI elements with new battle
        self.create_ui_elements(new_battle) 