from collections import defaultdict
import pygame
import battles
from scenes.scene import Scene
import pygame_gui
from scenes.events import BattleEditorSceneEvent, SandboxSceneEvent, SetupBattleSceneEvent, TestEditorSceneEvent
from progress_manager import ProgressManager
from ui_components.barracks_ui import BarracksUI, UnitCount

battle_swap_icon = pygame.image.load("assets/icons/BattleSwapIcon.png")

class SelectBattleScene(Scene):
    """The scene for selecting a battle."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager, progress_manager: ProgressManager):
        self.screen = screen
        self.progress_manager = progress_manager
        self.manager = manager
        self.create_buttons()

    def create_buttons(self) -> None:
        button_width = 200
        button_height = 64
        padding = 10
        icon_size = UnitCount.size
        
        # Add sandbox, editor and test editor buttons to the right side
        self.sandbox_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - button_width - padding, padding),
                (button_width, button_height)
            ),
            text="Sandbox Mode",
            manager=self.manager
        )
        
        self.editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 2 * button_width - 2 * padding, padding),
                (button_width, button_height)
            ),
            text="Battle Editor",
            manager=self.manager
        )

        self.test_editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 3 * button_width - 3 * padding, padding),
                (button_width, button_height)
            ),
            text="Test Editor",
            manager=self.manager
        )
        
        # Create scrollable container
        container_width = pygame.display.Info().current_w - 2 * padding
        container_height = pygame.display.Info().current_h - 225  # Leave space for other UI elements
        scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((padding, 100), (container_width, container_height)),
            manager=self.manager,
            allow_scroll_x=False,
        )

        # Calculate total height needed for content
        content_height = len(self.progress_manager.available_battles()) * (button_height + padding) + padding
        # Use max to ensure the container is at least as tall as its view area
        total_height = max(content_height, container_height)
        
        # Create a panel inside the scroll container to hold all content
        content_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (container_width, total_height)),
            manager=self.manager,
            container=scroll_container,
            object_id="#content_panel"
        )

        self.battle_buttons = []
        for i, battle_id in enumerate(self.progress_manager.available_battles()):
            y_pos = i * (button_height + padding) + padding
            x = pygame.display.Info().current_w // 2 - button_width // 2
            
            # Create battle button and store reference
            battle_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (x - padding, y_pos),
                    (button_width, button_height)
                ),
                text=battle_id,
                manager=self.manager,
                container=content_panel
            )
            self.battle_buttons.append(battle_button)
            
            x += button_width + padding
            solution = self.progress_manager.solutions.get(battle_id, None)
            
            # Show player's solution if it exists
            if solution is not None:
                unit_counts = defaultdict(int)
                for unit_type, _ in solution.unit_placements:
                    unit_counts[unit_type] += 1
                for unit_type, count in unit_counts.items():
                    UnitCount(
                        x_pos=x - padding,
                        y_pos=y_pos + button_height // 2 - icon_size // 2,
                        unit_type=unit_type,
                        count=count,
                        interactive=False,
                        manager=self.manager,
                        container=content_panel,
                        infinite=False,
                    )
                    x += icon_size + padding

            # Add swap icon and enemy units for both solved and unlocked battles
            swap_icon_size = 32
            pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (x - padding, y_pos + button_height // 2 - swap_icon_size // 2),
                    (swap_icon_size, swap_icon_size)
                ),
                image_surface=battle_swap_icon,
                manager=self.manager,
                container=content_panel
            )
            x += swap_icon_size + padding

            # Add enemy unit counts
            enemy_counts = defaultdict(int)
            for enemy_type, _ in battles.get_battle(battle_id).enemies:
                enemy_counts[enemy_type] += 1
            for unit_type, count in enemy_counts.items():
                UnitCount(
                    x_pos=x - padding,
                    y_pos=y_pos + button_height // 2 - icon_size // 2,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager,
                    container=content_panel,
                    infinite=False,
                )
                x += icon_size + padding

        self.barracks = BarracksUI(
            self.manager,
            self.progress_manager.available_units(current_battle_id=None),
            interactive=False,
            sandbox_mode=False,
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the select battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.sandbox_button:
                        pygame.event.post(SandboxSceneEvent(
                            ally_placements=[],
                            enemy_placements=[],
                            battle_id=None,
                            editor_scroll=None,    
                        ).to_event())
                    elif event.ui_element == self.editor_button:
                        pygame.event.post(BattleEditorSceneEvent(editor_scroll=0).to_event())
                    elif event.ui_element == self.test_editor_button:
                        pygame.event.post(TestEditorSceneEvent(editor_scroll=0).to_event())
                    elif event.ui_element in self.battle_buttons:
                        battle_id = event.ui_element.text
                        solution = self.progress_manager.solutions.get(battle_id, None)
                        ally_placements = solution.unit_placements if solution else []
                        pygame.event.post(
                            SetupBattleSceneEvent(
                                battle_id=battle_id,
                                ally_placements=ally_placements
                            ).to_event()
                        )
        
            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return True
