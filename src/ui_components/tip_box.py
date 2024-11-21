import pygame
import pygame_gui
from battles import Battle

class TipBox(pygame_gui.elements.UITextBox):
    def __init__(self, manager: pygame_gui.UIManager, battle: Battle) -> None:
        width = max(len(line) for line in battle.tip) * 8
        height = len(battle.tip) * 20
        super().__init__(
            html_text='<br>'.join(battle.tip),
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w//2, 10),
                (width, height)
            ),
            manager=manager,
            wrap_to_height=True,
            object_id="#tip_box"
        )
        # Center the tip box horizontally
        window_width = pygame.display.Info().current_w
        self.rect.centerx = window_width // 2
