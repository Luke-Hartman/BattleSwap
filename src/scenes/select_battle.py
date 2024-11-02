import pygame
from CONSTANTS import SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.scene import Scene
import pygame_gui
from scenes.events import SETUP_BATTLE_SCENE
from progress_manager import ProgressManager

class SelectBattleScene(Scene):
    """The scene for selecting a battle."""

    def __init__(self, screen: pygame.Surface, progress_manager: ProgressManager):
        self.screen = screen
        self.progress_manager = progress_manager
        self.manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.create_buttons()

    def create_buttons(self) -> None:
        button_width = 200
        button_height = 50
        button_spacing = 20
        start_y = 100

        for i, battle in enumerate(self.progress_manager.available_battles()):
            button_rect = pygame.Rect(
                (SCREEN_WIDTH // 2 - button_width // 2,
                 start_y + i * (button_height + button_spacing)),
                (button_width, button_height)
            )
            pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=battle,
                manager=self.manager
            )

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
        self.screen.fill((200, 200, 200))
        self.manager.draw_ui(self.screen)
        return True
