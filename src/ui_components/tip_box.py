import pygame
import pygame_gui
from battles import Battle

class TipBox(pygame_gui.elements.UITextBox):
    def __init__(self, manager: pygame_gui.UIManager, battle: Battle) -> None:
        super().__init__(
            html_text='<br>'.join(battle.tip),
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w//2, 10),
                (-1, -1)
            ),
            manager=manager,
            wrap_to_height=True
        )
        # Center the tip box horizontally
        window_width = pygame.display.Info().current_w
        self.rect.centerx = window_width // 2
