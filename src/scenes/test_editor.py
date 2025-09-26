"""Scene for editing and running test battles."""
from collections import defaultdict
from enum import Enum, auto
import pygame
import pygame_gui
from camera import Camera
from scenes.scene import Scene
from scenes.events import PreviousSceneEvent, SetupBattleSceneEvent
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from ui_components.unit_count import UnitCount
import battles
from auto_battle import simulate_battle, BattleOutcome
from ui_components.save_battle_dialog import SaveBattleDialog
from world_map_view import WorldMapView
from game_constants import gc
from keyboard_shortcuts import format_button_text, KeyboardShortcuts

class TestStatus(Enum):
    """Status of a test run."""
    NOT_RUN = auto()
    RUNNING = auto()
    PASSED = auto()
    FAILED = auto()
    TIMEOUT = auto()

class TestEditorScene(Scene):
    """Scene for editing and running test battles."""
    
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
        self.sandbox_buttons = {}
        self.delete_buttons = {}
        self.run_buttons = {}
        self.test_statuses = defaultdict(lambda: TestStatus.NOT_RUN)
        self.show_only_failures = False
        screen.fill((0, 0, 0))
        self.create_ui(editor_scroll)
    
    def create_ui(self, editor_scroll: float = 0.0) -> None:
        padding = 5
        inner_padding = 5
        button_height = 30
        top_panel_height = 40
        
        # Create scrollable container for the entire content
        container_width = pygame.display.Info().current_w - 2 * padding
        container_height = pygame.display.Info().current_h - padding
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((padding, 0), (container_width, container_height)),
            manager=self.manager
        )

        # Filter test battles based on show_only_failures
        test_battles = [b for b in battles.get_battles() if b.is_test]
        if self.show_only_failures:
            test_battles = [b for b in test_battles 
                           if self.test_statuses[b.id] in (TestStatus.FAILED, TestStatus.TIMEOUT)]

        # Calculate total height needed - match battle editor's panel height
        panel_height = 100  # Changed to match battle editor
        total_height = len(test_battles) * (panel_height + padding) + top_panel_height + padding

        # Explicitly set scrollable area dimensions
        self.scroll_container.set_scrollable_area_dimensions((container_width - 20, total_height))

        # Create a panel inside the scroll container to hold all content
        content_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (container_width - 20, total_height)),
            manager=self.manager,
            container=self.scroll_container,
            object_id="#content_panel"
        )

        # Top row buttons
        self.return_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((padding, padding), (100, button_height)),
            text=format_button_text("Return", KeyboardShortcuts.ESCAPE),
            manager=self.manager,
            container=content_panel
        )

        pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((padding + 110, padding), (120, button_height)),
            text="New Sandbox",
            manager=self.manager,
            container=content_panel
        )

        # Battle selection dropdown - showing non-test battles
        non_test_battles = [b for b in battles.get_battles() if not b.is_test]
        battle_options = ["Create test from..."] + [f"{b.id}" for b in non_test_battles]
        self.battle_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=battle_options,
            starting_option=battle_options[0],
            relative_rect=pygame.Rect((padding + 240, padding), (200, button_height)),
            manager=self.manager,
            container=content_panel
        )

        self.show_failures_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 270, padding),
                (130, button_height)
            ),
            text="Show All Tests" if self.show_only_failures else "Show Failures",
            manager=self.manager,
            container=content_panel
        )

        self.run_all_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 130, padding),
                (100, button_height)
            ),
            text="Run All",
            manager=self.manager,
            container=content_panel
        )

        # Calculate space needed for 5 units plus padding
        unit_section_width = 5 * (UnitCount.size + inner_padding) + inner_padding

        # Add each test's information
        for i, test in enumerate(test_battles):
            current_y = i * (panel_height + padding) + top_panel_height + padding
            
            # Create a container panel for this test
            test_panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect(
                    (padding, current_y),
                    (container_width - 40, panel_height)
                ),
                manager=self.manager,
                container=content_panel,
                object_id=f"#test_panel_{i}"
            )
            
            panel_width = container_width - 40

            # ID label - same position as battle editor
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (inner_padding, inner_padding),
                    (unit_section_width - 160, 20)
                ),
                text=f"ID: {test.id}",
                manager=self.manager,
                container=test_panel
            )

            # Edit and sandbox buttons - same position as battle editor
            self.edit_buttons[test.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (unit_section_width - 150, inner_padding),
                    (50, 20)
                ),
                text="Edit",
                manager=self.manager,
                container=test_panel
            )

            self.sandbox_buttons[test.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (unit_section_width - 90, inner_padding),
                    (90, 20)
                ),
                text="Sandbox",
                manager=self.manager,
                container=test_panel
            )



            # Test controls - where dependencies would be in battle editor
            status = self.test_statuses[test.id]
            status_colors = {
                TestStatus.NOT_RUN: ("#808080", "Not Run"),
                TestStatus.RUNNING: ("#FFA500", "Running"),
                TestStatus.PASSED: ("#00FF00", "Passed"),
                TestStatus.FAILED: ("#FF0000", "Failed"),
                TestStatus.TIMEOUT: ("#FFFF00", "Timeout")
            }
            color, text = status_colors[status]

            # Status section - in dependencies area
            dep_start_x = unit_section_width + 400  # Match battle editor position
            dep_y = inner_padding

            # Status text
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (dep_start_x + 25, dep_y),
                    (60, 20)
                ),
                text=text,
                manager=self.manager,
                container=test_panel
            )

            # Run button
            self.run_buttons[test.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (dep_start_x + 90, dep_y),
                    (50, 20)
                ),
                text="Run",
                manager=self.manager,
                container=test_panel
            )

            # Delete button - same position as battle editor
            self.delete_buttons[test.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (panel_width - 60 - inner_padding, inner_padding),
                    (60, 25)
                ),
                text="Delete",
                manager=self.manager,
                container=test_panel
            )

            # Unit preview section - same position as battle editor
            unit_y = 20 + (panel_height - 20 - UnitCount.size) // 2
            x = inner_padding

            # Display ally units
            ally_counts = defaultdict(int)
            if test.allies is not None:
                for ally_type, _ in test.allies:
                    ally_counts[ally_type] += 1
            
            for unit_type, count in ally_counts.items():
                UnitCount(
                    x_pos=x,
                    y_pos=unit_y,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager,
                    container=test_panel,
                    infinite=False,
                )
                x += UnitCount.size + inner_padding

            # VS label
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (x, unit_y),
                    (30, UnitCount.size)
                ),
                text="VS",
                manager=self.manager,
                container=test_panel
            )
            x += 40

            # Display enemy units
            enemy_counts = defaultdict(int)
            for enemy_type, _ in test.enemies:
                enemy_counts[enemy_type] += 1
            
            for unit_type, count in enemy_counts.items():
                UnitCount(
                    x_pos=x,
                    y_pos=unit_y,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager,
                    container=test_panel,
                    infinite=False,
                )
                x += UnitCount.size + inner_padding

        # Set scroll position
        self.scroll_container.vert_scroll_bar.start_percentage = editor_scroll

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the test editor scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            self.handle_escape(event)
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent(current_scene_id=id(self)).to_event())
                    elif event.ui_element.text == "New Sandbox":
                        pygame.event.post(
                            SetupBattleSceneEvent(
                                current_scene_id=id(self),
                                world_map_view=None,
                                battle_id=None,
                                sandbox_mode=True,
                                developer_mode=True,
                                is_corrupted=False,
                            ).to_event()
                        )
                    elif event.ui_element in self.edit_buttons.values():
                        battle_id = list(self.edit_buttons.keys())[
                            list(self.edit_buttons.values()).index(event.ui_element)
                        ]
                        battle = battles.get_battle_id(battle_id)
                        
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            battle.allies,
                            battle.enemies,
                            existing_battle_id=battle_id,
                            spell_placements=battle.spells,
                        )
                    elif event.ui_element in self.sandbox_buttons.values():
                        battle_id = list(self.sandbox_buttons.keys())[
                            list(self.sandbox_buttons.values()).index(event.ui_element)
                        ]
                        battle = battles.get_battle_id(battle_id)
                        battle.hex_coords = (0, 0)
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=[battle],
                            camera=Camera(),
                        )
                        pygame.event.post(
                            SetupBattleSceneEvent(
                                current_scene_id=id(self),
                                world_map_view=world_map_view,
                                battle_id=battle_id,
                                sandbox_mode=True,
                                developer_mode=True,
                                is_corrupted=False,
                            ).to_event()
                        )
                    elif event.ui_element in self.delete_buttons.values():
                        battle_id = list(self.delete_buttons.keys())[
                            list(self.delete_buttons.values()).index(event.ui_element)
                        ]
                        battles.delete_battle(battle_id)
                        self._rebuild_ui()
                    elif event.ui_element in self.run_buttons.values():
                        battle_id = list(self.run_buttons.keys())[
                            list(self.run_buttons.values()).index(event.ui_element)
                        ]
                        self._run_test(battle_id)
                    elif event.ui_element == self.run_all_button:
                        self._run_all_tests()
                    elif event.ui_element == self.show_failures_button:
                        self.show_only_failures = not self.show_only_failures
                        self._rebuild_ui()
                    elif hasattr(self, 'save_dialog') and self.save_dialog:
                        if event.ui_element == self.save_dialog.save_battle_button:
                            self.save_dialog.save_battle(is_test=True)
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
                elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == self.battle_dropdown and event.text != "Create test from...":
                        battle = battles.get_battle_id(event.text).model_copy()

                        battle.id = battle.id + " (test)"
                        battle.is_test = True
                        battles.add_battle(battle)
                        self.battle_dropdown.selected_option = "Create test from..."
                        self._rebuild_ui()
            self.manager.process_events(event)
        
        self.manager.update(time_delta)
        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)

    def _close_scene_windows(self) -> bool:
        """Close any open windows specific to the test editor scene."""
        windows_closed = False
        
        # Check for save dialog
        if hasattr(self, 'save_dialog') and self.save_dialog is not None:
            self.save_dialog.kill()
            self.save_dialog = None
            windows_closed = True
            
        # Fall back to base class behavior and combine results
        return super()._close_scene_windows() or windows_closed

    def _get_scroll_percentage(self) -> float:
        """Get the current scroll position as a percentage."""
        for element in self.manager.get_sprite_group():
            if isinstance(element, pygame_gui.elements.UIScrollingContainer):
                if element.vert_scroll_bar:
                    return (element.vert_scroll_bar.scroll_position /
                           element.vert_scroll_bar.scrollable_height)
        return 0.0

    def _rebuild_ui(self) -> None:
        """Rebuild the UI."""
        scroll_percentage = self._get_scroll_percentage()
        self.manager.clear_and_reset()
        self.create_ui(scroll_percentage)

    def _run_test(self, test_id: str) -> None:
        """Run a single test."""
        test = battles.get_battle_id(test_id)
        if not test or not test.allies:
            return

        self.test_statuses[test_id] = TestStatus.RUNNING
        self._rebuild_ui()  # Update UI to show running status

        outcome = simulate_battle(
            ally_placements=test.allies,
            enemy_placements=test.enemies,
            max_duration=60,  # 60 second timeout
        )

        if outcome == BattleOutcome.TEAM1_VICTORY:
            self.test_statuses[test_id] = TestStatus.PASSED
        elif outcome == BattleOutcome.TEAM2_VICTORY:
            self.test_statuses[test_id] = TestStatus.FAILED
        else:  # TIMEOUT
            self.test_statuses[test_id] = TestStatus.TIMEOUT

        self._rebuild_ui()  # Update UI to show final status

    def _run_all_tests(self) -> None:
        """Run all tests in sequence."""
        test_battles = [b for b in battles.get_battles() if b.is_test]
        
        # Reset all test statuses
        for test in test_battles:
            self.test_statuses[test.id] = TestStatus.NOT_RUN
        self._rebuild_ui()

        # Run each test
        for test in test_battles:
            self._run_test(test.id) 