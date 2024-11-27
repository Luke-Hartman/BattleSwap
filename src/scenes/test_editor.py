"""Scene for editing and running test battles."""
from collections import defaultdict
from enum import Enum, auto
import pygame
import pygame_gui
from scenes.scene import Scene
from scenes.events import SandboxSceneEvent, SelectBattleSceneEvent
from ui_components.barracks_ui import UnitCount
import battles
from auto_battle import simulate_battle, BattleOutcome
from ui_components.save_battle_dialog import SaveBattleDialog

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
        self.screen = screen
        self.manager = manager
        self.edit_buttons = {}
        self.sandbox_buttons = {}
        self.delete_buttons = {}
        self.run_buttons = {}
        self.test_statuses = defaultdict(lambda: TestStatus.NOT_RUN)
        screen.fill((0, 0, 0))
        self.create_ui(editor_scroll)
    
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

        # Run all button at top-right
        self.run_all_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 110, padding),
                (100, button_height)
            ),
            text="Run All",
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

        # Get all test battles
        test_battles = [b for b in battles.get_battles() if b.is_test]

        # Calculate total height needed - match battle editor's panel height
        panel_height = 100  # Changed to match battle editor
        total_height = len(test_battles) * (panel_height + padding) + padding

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

        # Add each test's information
        for i, test in enumerate(test_battles):
            current_y = i * (panel_height + padding)
            
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

            # Tip text - same position and size as battle editor
            if test.tip:
                tip_box = pygame_gui.elements.UITextBox(
                    relative_rect=pygame.Rect(
                        (unit_section_width, inner_padding),
                        (300, panel_height - 2 * inner_padding)
                    ),
                    html_text="<br>".join(test.tip),
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
                    (container_width - 100, inner_padding),
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
        scroll_container.vert_scroll_bar.start_percentage = editor_scroll

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the test editor scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element.text == "Return":
                        pygame.event.post(SelectBattleSceneEvent().to_event())
                    elif event.ui_element.text == "New Sandbox":
                        scroll_percentage = self._get_scroll_percentage()
                        pygame.event.post(
                            SandboxSceneEvent(
                                ally_placements=[],
                                enemy_placements=[],
                                battle_id=None,
                                editor_scroll=scroll_percentage
                            ).to_event()
                        )
                    elif event.ui_element == self.run_all_button:
                        self._run_all_tests()
                    elif event.ui_element in self.run_buttons.values():
                        test_id = list(self.run_buttons.keys())[
                            list(self.run_buttons.values()).index(event.ui_element)
                        ]
                        self._run_test(test_id)
                    elif event.ui_element in self.edit_buttons.values():
                        battle_id = list(self.edit_buttons.keys())[
                            list(self.edit_buttons.values()).index(event.ui_element)
                        ]
                        test = battles.get_battle(battle_id)
                        
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            ally_placements=test.allies,
                            enemy_placements=test.enemies,
                            existing_battle_id=battle_id,
                        )
                    elif event.ui_element in self.sandbox_buttons.values():
                        test_id = list(self.sandbox_buttons.keys())[
                            list(self.sandbox_buttons.values()).index(event.ui_element)
                        ]
                        test = battles.get_battle(test_id)
                        if test:
                            scroll_percentage = self._get_scroll_percentage()
                            pygame.event.post(
                                SandboxSceneEvent(
                                    ally_placements=test.allies if test.allies else [],
                                    enemy_placements=test.enemies,
                                    battle_id=test_id,
                                    editor_scroll=scroll_percentage
                                ).to_event()
                            )
                    elif event.ui_element in self.delete_buttons.values():
                        test_id = list(self.delete_buttons.keys())[
                            list(self.delete_buttons.values()).index(event.ui_element)
                        ]
                        battles.delete_battle(test_id)
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

            self.manager.process_events(event)
        
        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return True

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
        test = battles.get_battle(test_id)
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