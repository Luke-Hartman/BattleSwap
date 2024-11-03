from collections import defaultdict
import pygame
import battles
from scenes.scene import Scene
import pygame_gui
from scenes.events import SETUP_BATTLE_SCENE
from progress_manager import ProgressManager
from ui_components.barracks_ui import BarracksUI, UnitCount
from entities.units import unit_icon_surfaces

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
        start_y = 100
        padding = 10
        icon_size = UnitCount.size


        for i, battle_id in enumerate(self.progress_manager.available_battles()):
            y_center = start_y + i * 84 + padding
            x = pygame.display.Info().current_w // 2 - button_width // 2
            pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                (x, y_center - button_height // 2),
                (button_width, button_height)
            ),
                text=battle_id,
                manager=self.manager
            )
            x += button_width + padding
            solution = self.progress_manager.solutions.get(battle_id, None)
            if solution is None:
                continue

            unit_counts = defaultdict(int)
            for unit_type, _ in solution.unit_placements:
                unit_counts[unit_type] += 1
            for unit_type, count in unit_counts.items():
                UnitCount(
                    x_pos=x,
                    y_pos=y_center - icon_size // 2,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager
                )
                x += icon_size + padding

            swap_icon_size = 32
            pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect((x, y_center - swap_icon_size // 2), (swap_icon_size, swap_icon_size)),
                image_surface=battle_swap_icon,
                manager=self.manager
            )
            x += swap_icon_size + padding

            enemy_counts = defaultdict(int)
            for enemy_type, _ in battles.get_battle(battle_id).enemies:
                enemy_counts[enemy_type] += 1
            for unit_type, count in enemy_counts.items():
                UnitCount(
                    x_pos=x,
                    y_pos=y_center - icon_size // 2,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager
                )
                x += icon_size + padding
            
        self.barracks = BarracksUI(self.manager, self.progress_manager.available_units(), interactive=False)

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the select battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    pygame.event.post(
                        pygame.event.Event(
                            SETUP_BATTLE_SCENE,
                            battle_id=event.ui_element.text,
                            potential_solution=self.progress_manager.solutions.get(event.ui_element.text, None)
                        )
                    )
            
            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return True
