from collections import defaultdict
import pygame
import pygame_gui
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scenes.scene import Scene
from scenes.events import SandboxSceneEvent, SelectBattleSceneEvent
from ui_components.barracks_ui import UnitCount
from ui_components.save_battle_dialog import SaveBattleDialog
import battles
from typing import Dict

class BattleEditorScene(Scene):
    """Scene for editing and arranging battle levels."""
    
    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        editor_scroll: float = 0.0
    ) -> None:
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.edit_buttons = {}
        self.top_buttons = {}
        self.up_buttons = {}
        self.down_buttons = {}
        self.bottom_buttons = {}
        self.delete_buttons = {}
        self.move_after_dropdowns: Dict[str, pygame_gui.elements.UIDropDownMenu] = {}
        self.dependency_remove_buttons: Dict[str, Dict[str, pygame_gui.elements.UIButton]] = {}
        self.dependency_add_dropdowns: Dict[str, pygame_gui.elements.UIDropDownMenu] = {}
        self.edit_sandbox_buttons = {}
        self.depend_on_prev_buttons = {}
        screen.fill((0, 0, 0))
        self.create_ui(editor_scroll)
    
    def _rebuild_ui(self) -> None:
        """Rebuild the UI."""
        scroll_percentage = self._get_scroll_percentage()
        self.manager.clear_and_reset()
        self.create_ui(scroll_percentage)

    def create_ui(self, editor_scroll: float = 0.0) -> None:
        padding = 5
        inner_padding = 5
        button_height = 30
        
        # Return button at top-left
        pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((padding, padding), (100, button_height)),
            text="Return",
            manager=self.manager
        )
        
        # New Sandbox button next to Return
        pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((padding + 110, padding), (120, button_height)),
            text="New Sandbox",
            manager=self.manager
        )
        
        # Create scrollable container
        container_width = pygame.display.Info().current_w - 2 * padding
        container_height = pygame.display.Info().current_h - 45
        scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((padding, 40), (container_width, container_height)),
            manager=self.manager,
            allow_scroll_x=False,
        )

        # Get all non-test battles
        battles_list = [b for b in battles.get_battles() if not b.is_test]

        # Calculate total height needed
        panel_height = 100
        total_height = len(battles_list) * (panel_height + padding) + padding

        # Explicitly set scrollable area dimensions
        scroll_container.set_scrollable_area_dimensions((container_width - 20, total_height))

        # Create a panel inside the scroll container to hold all content
        content_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (container_width - 20, total_height)),
            manager=self.manager,
            container=scroll_container,
            object_id="#content_panel"
        )

        # Calculate space needed for 5 units plus padding
        unit_section_width = 5 * (UnitCount.size + inner_padding) + inner_padding

        # Add each battle's information
        for i, battle in enumerate(battles_list):
            current_y = i * (panel_height + padding)
            
            # Create a container panel for this battle
            battle_panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect(
                    (padding, current_y),
                    (container_width - 40, panel_height)
                ),
                manager=self.manager,
                container=content_panel,
                object_id=f"#battle_panel_{i}"
            )
            
            panel_width = container_width - 40

            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (inner_padding, inner_padding),
                    (unit_section_width - 160, 20)
                ),
                text=f"ID: {battle.id}",
                manager=self.manager,
                container=battle_panel
            )
            
            self.edit_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (unit_section_width - 150, inner_padding),
                    (50, 20)
                ),
                text="Edit",
                manager=self.manager,
                container=battle_panel
            )
            
            self.edit_sandbox_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (unit_section_width - 90, inner_padding),
                    (90, 20)
                ),
                text="Sandbox",
                manager=self.manager,
                container=battle_panel
            )
            
            # Enemy units (below battle ID)
            enemy_counts = defaultdict(int)
            for enemy_type, _ in battle.enemies:
                enemy_counts[enemy_type] += 1
            
            # Center the units vertically in the remaining space
            unit_section_height = panel_height - 20  # Space below the battle ID
            unit_y = 20 + (unit_section_height - UnitCount.size) // 2  # Center units in remaining space
            x = inner_padding
            
            # Display existing enemy units
            for unit_type, count in enemy_counts.items():
                UnitCount(
                    x_pos=x,
                    y_pos=unit_y,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager,
                    container=battle_panel,
                    infinite=False,
                )
                x += UnitCount.size + inner_padding
            
            # Tips (right side) - adjusted to account for fixed unit section width
            tip_width = 300
            tip_start_x = unit_section_width
            tip_box = pygame_gui.elements.UITextBox(
                html_text='<br>'.join(battle.tip),
                relative_rect=pygame.Rect(
                    (tip_start_x, inner_padding),
                    (tip_width, panel_height - 2 * inner_padding)
                ),
                manager=self.manager,
                container=battle_panel
            )

            # Order buttons
            button_width = 60
            button_height = 20
            button_x = tip_start_x + tip_width + inner_padding
            button_spacing = 3

            # Top button
            self.top_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (button_x, inner_padding),
                    (button_width, button_height)
                ),
                text="top",
                manager=self.manager,
                container=battle_panel
            )

            # Up button
            self.up_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (button_x, inner_padding + button_height + button_spacing),
                    (button_width, button_height)
                ),
                text="up",
                manager=self.manager,
                container=battle_panel
            )

            # Down button
            self.down_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (button_x, inner_padding + 2 * (button_height + button_spacing)),
                    (button_width, button_height)
                ),
                text="down",
                manager=self.manager,
                container=battle_panel
            )

            # Bottom button
            self.bottom_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (button_x, inner_padding + 3 * (button_height + button_spacing)),
                    (button_width, button_height)
                ),
                text="bottom",
                manager=self.manager,
                container=battle_panel
            )

            # Move after dropdown
            dropdown_width = 150
            dropdown_height = 25

            # Calculate absolute position relative to content_panel
            battle_panel_rect = battle_panel.get_relative_rect()
            dropdown_x = battle_panel_rect.left + button_x + button_width + inner_padding
            dropdown_y = battle_panel_rect.top + inner_padding

            # Create list of battle options, excluding current battle
            battle_options = ["-- Move after --"] + [
                b.id for b in battles_list if b.id != battle.id
            ]

            self.move_after_dropdowns[battle.id] = pygame_gui.elements.UIDropDownMenu(
                options_list=battle_options,
                starting_option="-- Move after --",
                relative_rect=pygame.Rect(
                    (dropdown_x, dropdown_y),
                    (dropdown_width, dropdown_height)
                ),
                manager=self.manager,
                container=content_panel
            )

            # Dependencies UI
            dep_start_x = dropdown_x + dropdown_width + inner_padding
            dep_y = inner_padding

            # Display current dependencies with remove buttons
            self.dependency_remove_buttons[battle.id] = {}
            dep_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (dep_start_x, dep_y),
                    (100, 25)
                ),
                text="Dependencies:",
                manager=self.manager,
                container=battle_panel
            )
            
            # Start dependencies to the right of the label
            dep_x = dep_start_x + 105  # Move past the label
            
            # Display dependencies horizontally
            for dep_battle_id in battle.dependencies:
                # Create text box for battle ID with dynamic width
                dep_text = pygame_gui.elements.UITextBox(
                    html_text=dep_battle_id,
                    relative_rect=pygame.Rect(
                        (dep_x, dep_y),
                        (-1, 30)  # Height fixed, width will be calculated
                    ),
                    manager=self.manager,
                    container=battle_panel,
                )
                
                # Position remove button right after the text box
                remove_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(
                        (dep_x + dep_text.rect.width + 5, dep_y),
                        (70, 25)
                    ),
                    text="Remove",
                    manager=self.manager,
                    container=battle_panel
                )
                self.dependency_remove_buttons[battle.id][dep_battle_id] = remove_button
                
                # Move right for next dependency, using actual width of elements
                dep_x += dep_text.rect.width + 80  # 75 for button width + 5 padding

            # After dependencies section, add delete button at far right
            delete_x = battle_panel_rect.right - 70
            self.delete_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (delete_x, inner_padding),
                    (60, 25)
                ),
                text="Delete",
                manager=self.manager,
                container=battle_panel,
            )

            # Add dependency dropdown (position it below the dependencies)
            add_dep_options = ["-- Add dependency --"] + [
                b.id for b in battles_list
                if b.id != battle.id and b.id not in battle.dependencies
            ]
            if len(add_dep_options) > 1:  # Only show if there are battles to add
                # Calculate absolute position relative to content_panel
                dropdown_x = battle_panel_rect.left + dep_start_x
                dropdown_y = battle_panel_rect.top + dep_y + 30  # Position below the dependencies

                self.dependency_add_dropdowns[battle.id] = pygame_gui.elements.UIDropDownMenu(
                    options_list=add_dep_options,
                    starting_option="-- Add dependency --",
                    relative_rect=pygame.Rect(
                        (dropdown_x, dropdown_y),
                        (185, 25)
                    ),
                    manager=self.manager,
                    container=content_panel
                )

                # Add "depend on prev" button if this isn't the first battle
                if i > 0:
                    self.depend_on_prev_buttons[battle.id] = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect(
                            (dep_start_x + 190, dep_y + 30),
                            (120, 25)
                        ),
                        text="depend on prev",
                        manager=self.manager,
                        container=battle_panel
                    )

        # Set scroll position
        scroll_container.vert_scroll_bar.start_percentage = editor_scroll
    
    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle editor scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element.text == "Return":
                        pygame.event.post(SelectBattleSceneEvent().to_event())
                    elif event.ui_element.text == "New Sandbox":
                        pygame.event.post(
                            SandboxSceneEvent(
                                ally_placements=[],
                                enemy_placements=[],
                                battle_id=None,
                            ).to_event()
                        )
                    elif event.ui_element in self.edit_buttons.values():
                        battle_id = list(self.edit_buttons.keys())[list(self.edit_buttons.values()).index(event.ui_element)]
                        battle = battles.get_battle(battle_id)
                        
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            battle.allies,
                            battle.enemies,
                            existing_battle_id=battle_id,
                        )
                    # Handle order buttons
                    elif event.ui_element in self.top_buttons.values():
                        battle_id = list(self.top_buttons.keys())[list(self.top_buttons.values()).index(event.ui_element)]
                        battles.move_battle_to_top(battle_id)
                        self._rebuild_ui()
                    elif event.ui_element in self.up_buttons.values():
                        battle_id = list(self.up_buttons.keys())[list(self.up_buttons.values()).index(event.ui_element)]
                        battles.move_battle_up(battle_id)
                        self._rebuild_ui()
                    elif event.ui_element in self.down_buttons.values():
                        battle_id = list(self.down_buttons.keys())[list(self.down_buttons.values()).index(event.ui_element)]
                        battles.move_battle_down(battle_id)
                        self._rebuild_ui()
                    elif event.ui_element in self.bottom_buttons.values():
                        battle_id = list(self.bottom_buttons.keys())[list(self.bottom_buttons.values()).index(event.ui_element)]
                        battles.move_battle_to_bottom(battle_id)
                        self._rebuild_ui()
                    # Handle delete buttons
                    elif event.ui_element in self.delete_buttons.values():
                        battle_id = list(self.delete_buttons.keys())[
                            list(self.delete_buttons.values()).index(event.ui_element)
                        ]
                        battles.delete_battle(battle_id)
                        self._rebuild_ui()
                    # Handle edit sandbox buttons
                    elif event.ui_element in self.edit_sandbox_buttons.values():
                        battle_id = list(self.edit_sandbox_buttons.keys())[
                            list(self.edit_sandbox_buttons.values()).index(event.ui_element)
                        ]
                        battle = battles.get_battle(battle_id)
                        scroll_percentage = self._get_scroll_percentage()
                        pygame.event.post(
                            SandboxSceneEvent(
                                ally_placements=[],
                                enemy_placements=battle.enemies,
                                battle_id=battle_id,
                                editor_scroll=scroll_percentage
                            ).to_event()
                        )
                    # Handle save dialog buttons
                    elif hasattr(self, 'save_dialog') and self.save_dialog:
                        if event.ui_element == self.save_dialog.save_battle_button:
                            self.save_dialog.save_battle(is_test=False)
                            self.save_dialog.kill()
                            self.save_dialog = None
                            self._rebuild_ui()
                        elif event.ui_element == self.save_dialog.save_test_button:
                            self.save_dialog.save_battle(is_test=True)
                            self.save_dialog.kill()
                            self.save_dialog = None
                            self._rebuild_ui()
                        elif event.ui_element == self.save_dialog.cancel_button:
                            self.save_dialog.kill()
                            self.save_dialog = None
                    # Add this section to handle the depend on prev button
                    elif event.ui_element in self.depend_on_prev_buttons.values():
                        battle_id = list(self.depend_on_prev_buttons.keys())[
                            list(self.depend_on_prev_buttons.values()).index(event.ui_element)
                        ]
                        battles.depend_on_previous_battle(battle_id)
                        self._rebuild_ui()
                    # Handle dependency remove buttons
                    for battle_id, remove_buttons in self.dependency_remove_buttons.items():
                        if event.ui_element in remove_buttons.values():
                            dependency_id = list(remove_buttons.keys())[
                                list(remove_buttons.values()).index(event.ui_element)
                            ]
                            previous_battle = battles.get_battle(battle_id)
                            updated_battle = previous_battle.model_copy()
                            updated_battle.dependencies.remove(dependency_id)
                            battles.update_battle(previous_battle, updated_battle)
                            self._rebuild_ui()
                            break
                elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    # Handle move after dropdown
                    for battle_id, dropdown in self.move_after_dropdowns.items():
                        if event.ui_element == dropdown and event.text != "-- Move after --":
                            target_battle_id = event.text
                            battles.move_battle_after(battle_id, target_battle_id)
                            self._rebuild_ui()
                            break
                    
                    # Handle dependency add dropdown
                    for battle_id, dropdown in self.dependency_add_dropdowns.items():
                        if event.ui_element == dropdown and event.text != "-- Add dependency --":
                            previous_battle = battles.get_battle(battle_id)
                            if event.text not in previous_battle.dependencies:
                                updated_battle = previous_battle.model_copy()
                                updated_battle.dependencies.append(event.text)
                                battles.update_battle(previous_battle, updated_battle)
                                self._rebuild_ui()
                                break

            self.manager.process_events(event)
        
        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)

    def _get_scroll_percentage(self) -> float:
        """Get the current scroll position as a percentage."""
        for element in self.manager.get_sprite_group():
            if isinstance(element, pygame_gui.elements.UIScrollingContainer):
                if element.vert_scroll_bar:
                    return (element.vert_scroll_bar.scroll_position /
                           element.vert_scroll_bar.scrollable_height)
        return 0.0