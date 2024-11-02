import pygame
import pygame_gui
from battles import Battle

class TipBox(pygame_gui.elements.UITextBox):
    def __init__(self, manager: pygame_gui.UIManager, battle: Battle) -> None:
        width = 10 + 7.5 * max(len(tip) for tip in battle.tip)
        height = 12 + 26*len(battle.tip)
        super().__init__(
            html_text='<br>'.join(battle.tip),
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w//2 - width//2, 10),
                (width, height)
            ),
            manager=manager
        )