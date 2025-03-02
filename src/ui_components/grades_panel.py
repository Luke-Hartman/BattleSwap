"""UI component for displaying grade information."""

from typing import Optional, Dict
import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel, UIButton
from pygame_gui.windows import UIMessageWindow
from pygame_gui.core import UIContainer
from pygame_gui.core import ObjectID

import battles
from progress_manager import progress_manager, calculate_points_for_units
from entities.units import UnitType
from components.team import TeamType
from scene_utils import get_unit_placements
from unit_values import unit_values

class GradesPanel(UIPanel):
    """Panel showing grade information in the barracks."""
    
    def __init__(
        self,
        relative_rect: pygame.Rect,
        manager: pygame_gui.UIManager,
        current_battle: Optional[battles.Battle] = None,
        container: Optional[pygame_gui.core.UIContainer] = None,
        is_setup_mode: bool = False,
    ):
        self.collapsed_height = relative_rect.height
        self.expanded_height = relative_rect.height + 230  # Increased space for grade details
        self.is_expanded = False
        self.base_rect = relative_rect.copy()  # Store the original rect
        self.is_setup_mode = is_setup_mode
        
        super().__init__(
            relative_rect=relative_rect,
            manager=manager,
            container=container,
            object_id='#grades_panel'
        )
        
        # Store manager for later use
        self.manager = manager
        
        # Create labels with more compact layout
        self.y_offset = 5  # Start closer to top
        self.label_height = 25  # Slightly smaller height
        self.label_spacing = 5  # Reduced spacing
        self.side_margin = 15  # Margin for both sides
        
        # Create the UI elements
        self.create_ui_elements(current_battle)

    def create_ui_elements(self, current_battle: Optional[battles.Battle]) -> None:
        """Create all UI elements with the current battle information."""
        # Calculate total points used in campaign
        campaign_points = 0
        for battle in battles.get_battles():
            if not battle.grades or battle.hex_coords not in progress_manager.solutions:
                continue
            solution = progress_manager.solutions[battle.hex_coords]
            campaign_points += calculate_points_for_units(solution.unit_placements)
        
        y_offset = self.y_offset
        
        # Battle-specific information first (always show, but empty if no battle)
        if current_battle and current_battle.grades:
            if self.is_setup_mode:
                # In setup mode, use currently deployed units
                current_units = get_unit_placements(TeamType.TEAM1, current_battle.hex_coords)
                points_used = calculate_points_for_units(current_units)
                grade = current_battle.grades.get_grade(points_used)
                battle_points = str(points_used)
                battle_grade = grade
            elif current_battle.hex_coords in progress_manager.solutions:
                # In normal mode, use saved solution
                points_used = calculate_points_for_units(current_battle.allies or [])
                grade = current_battle.grades.get_grade(points_used)
                battle_points = str(points_used)
                battle_grade = grade
            else:
                battle_points = "-"
                battle_grade = "-"
        else:
            battle_points = "-"
            battle_grade = "-"
            
        # Battle row
        self.battle_points_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"Battle: {battle_points}",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        
        self.battle_grade_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"Grade: {battle_grade}",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@right_aligned_text")
        )
        y_offset += self.label_height + self.label_spacing

        # Create battle grade details if expanded
        if self.is_expanded:
            grades = ['A', 'B', 'C', 'D']
            self.battle_grade_rows = []
            
            for grade in grades:
                is_current_grade = battle_grade == grade if battle_grade else False
                
                if current_battle and current_battle.grades:
                    cutoff = getattr(current_battle.grades, f"{grade.lower()}_cutoff")
                    text = f"{grade}: {cutoff}"
                else:
                    text = f"{grade}: -"
                
                row = UILabel(
                    relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
                    text=text,
                    manager=self.manager,
                    container=self,
                    object_id=ObjectID(class_id="@grade_row_current" if is_current_grade else "@grade_row")
                )
                self.battle_grade_rows.append(row)
                y_offset += self.label_height + 2

            y_offset += self.label_spacing * 2  # Extra spacing between battle and campaign sections

        # Campaign row
        overall_grade = progress_manager.calculate_overall_grade()
        self.points_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"Campaign: {campaign_points}",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@left_aligned_text")
        )
        
        self.overall_grade_label = UILabel(
            relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
            text=f"Grade: {overall_grade}",
            manager=self.manager,
            container=self,
            object_id=ObjectID(class_id="@right_aligned_text")
        )
        y_offset += self.label_height + self.label_spacing

        # Create campaign grade details if expanded
        if self.is_expanded:
            cutoffs = progress_manager.get_overall_grade_cutoffs()
            self.campaign_grade_rows = []
            grades = ['A', 'B', 'C', 'D']
            
            for grade in grades:
                is_current_grade = overall_grade == grade
                
                if cutoffs:
                    text = f"{grade}: {cutoffs[grade.lower()]}"
                else:
                    text = f"{grade}: -"
                
                row = UILabel(
                    relative_rect=pygame.Rect((self.side_margin, y_offset), (self.rect.width - 2*self.side_margin, self.label_height)),
                    text=text,
                    manager=self.manager,
                    container=self,
                    object_id=ObjectID(class_id="@grade_row_current" if is_current_grade else "@grade_row")
                )
                self.campaign_grade_rows.append(row)
                y_offset += self.label_height + 2

        # Add button at the bottom
        button_y = self.rect.height - self.label_height - self.y_offset
        button_text = "Collapse" if self.is_expanded else "Expand"
        self.cutoffs_button = UIButton(
            relative_rect=pygame.Rect((self.side_margin, button_y), (self.rect.width - 2 * self.side_margin, self.label_height)),
            text=button_text,
            manager=self.manager,
            container=self
        )
        
        # Store current battle for grade cutoffs
        self.current_battle = current_battle

    def kill_ui_elements(self) -> None:
        """Kill all UI elements."""
        self.battle_points_label.kill()
        self.battle_grade_label.kill()
        self.points_label.kill()
        self.overall_grade_label.kill()
        self.cutoffs_button.kill()
        
        if hasattr(self, 'battle_grade_rows'):
            for row in self.battle_grade_rows:
                row.kill()
        if hasattr(self, 'campaign_grade_rows'):
            for row in self.campaign_grade_rows:
                row.kill()

    def toggle_expansion(self) -> None:
        """Toggle between expanded and collapsed states."""
        self.is_expanded = not self.is_expanded
        
        # Calculate new height and position
        new_height = self.expanded_height if self.is_expanded else self.collapsed_height
        new_y = self.base_rect.bottom - new_height  # Keep bottom fixed, adjust top
        
        # Update panel position and height
        self.set_position((self.base_rect.x, new_y))
        self.set_dimensions((self.rect.width, new_height))
        
        # Recreate UI elements
        self.kill_ui_elements()
        self.create_ui_elements(self.current_battle)

    def update_battle(self, new_battle: Optional[battles.Battle]) -> None:
        """Update the displayed battle information."""
        # Kill all existing UI elements
        self.kill_ui_elements()
        
        # Recreate UI elements with new battle
        self.create_ui_elements(new_battle)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events."""
        if (event.type == pygame_gui.UI_BUTTON_PRESSED and 
            event.ui_element == self.cutoffs_button):
            self.toggle_expansion()
            return True
        return False 