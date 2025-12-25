"""UI component for displaying progress information."""

from typing import Optional, Dict
import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UITextBox
from pygame_gui.core import ObjectID

import battles
from progress_manager import HexLifecycleState, calculate_points_for_units, progress_manager
from components.team import TeamType
from scene_utils import get_unit_placements
from game_constants import gc
from ui_components.game_data import GlossaryEntryType
from point_values import item_values, spell_values

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
        self.margin = 10
        
        # Create the UI elements
        self.is_setup_mode = is_setup_mode
        self.create_ui_elements(current_battle)

    def create_ui_elements(self, current_battle: Optional[battles.Battle]) -> None:
        """Create all UI elements with the current battle information."""
        player_points = "-"
        enemy_points = "-"
        
        # Battle points information
        if current_battle:
            hex_state = progress_manager.get_hex_state(current_battle.hex_coords)
            if self.is_setup_mode:
                # In setup mode, use currently deployed units
                current_units = get_unit_placements(TeamType.TEAM1, current_battle)
                player_points = calculate_points_for_units(current_units, is_enemy=False)
                enemy_points = calculate_points_for_units(
                    current_battle.enemies or [],
                    is_enemy=True,
                    hex_coords=current_battle.hex_coords
                )
            elif current_battle.hex_coords in progress_manager.solutions:
                # In normal mode, use saved solution
                player_points = calculate_points_for_units(current_battle.allies or [], is_enemy=False)
                enemy_points = calculate_points_for_units(
                    current_battle.enemies or [],
                    is_enemy=True,
                    hex_coords=current_battle.hex_coords
                )
            elif hex_state != HexLifecycleState.FOGGED:
                player_points = "-"
                enemy_points = calculate_points_for_units(
                    current_battle.enemies or [],
                    is_enemy=True,
                    hex_coords=current_battle.hex_coords
                )

        # Barracks info - calculate unused points for units, items, and spells
        barracks_units = []
        for unit_type, count in progress_manager.available_units(current_battle=current_battle).items():
            barracks_units.extend([(unit_type, (0, 0), [])] * count)
        unit_points = calculate_points_for_units(barracks_units, is_enemy=False)
        
        available_items = progress_manager.available_items(current_battle=current_battle)
        item_points = sum(item_values[item_type] * count for item_type, count in available_items.items())
        
        available_spells = progress_manager.available_spells(current_battle=current_battle)
        spell_points = sum(spell_values[spell_type] * count for spell_type, count in available_spells.items())
        
        unused_points = unit_points + item_points + spell_points

        # Campaign completion stats
        denominator = 2 * len([b for b in battles.get_battles() if not b.is_test])
        numerator = 0
        for solution in progress_manager.solutions.values():
            if solution.solved_corrupted:
                numerator += 2
            else:
                numerator += 1
        percentage = int(numerator / denominator * 100)
        
        # Corruption info - use first corruption threshold if no corruption has happened yet
        has_been_corrupted = any(
            state in [HexLifecycleState.CORRUPTED, HexLifecycleState.RECLAIMED]
            for state in progress_manager.hex_states.values()
        )
        corruption_threshold = gc.FIRST_CORRUPTION_TRIGGER_POINTS if not has_been_corrupted else gc.CORRUPTION_TRIGGER_POINTS
        
        # Create HTML content with clickable links
        points_link = f"<a href='{GlossaryEntryType.POINTS.value}'>pts</a>"
        corruption_link = f"<a href='{GlossaryEntryType.CORRUPTION.value}'>corrupts</a>"
        
        # Format player_points and enemy_points, handling the "-" case
        if player_points == "-":
            player_points_text = f"- pts"
        else:
            player_points_text = f"{player_points} pts"
            
        if enemy_points == "-":
            enemy_points_text = f"- pts"
        else:
            enemy_points_text = f"{enemy_points} pts"
        
        completion_link = f"<a href='progress_details'>{percentage}% completion</a>"
        
        html_content = f"""{player_points_text} vs {enemy_points_text}
{unused_points} pts unused
({corruption_threshold} {points_link} unused {corruption_link})
{completion_link}"""
        
        # Create single text box with all content
        self.info_text = UITextBox(
            relative_rect=pygame.Rect((self.margin, 5), (self.rect.width - 2*self.margin, self.rect.height - 20)),
            html_text=html_content,
            manager=self.manager,
            container=self,
            wrap_to_height=True,
        )

    def kill_ui_elements(self) -> None:
        """Kill all UI elements."""
        self.info_text.kill()

    def update_battle(self, new_battle: Optional[battles.Battle]) -> None:
        """Update the displayed battle information."""
        # Kill all existing UI elements
        self.kill_ui_elements()
        
        # Recreate UI elements with new battle
        self.create_ui_elements(new_battle)