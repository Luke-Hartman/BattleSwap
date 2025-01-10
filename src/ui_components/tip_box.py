import pygame
import pygame_gui
from battles import Battle
from ui_components.text_box import TextBox

class TipBox(TextBox):
    def __init__(self, manager: pygame_gui.UIManager, battle: Battle) -> None:
        super().__init__(
            strings=battle.tip,
            top_center_pos=(pygame.display.Info().current_w//2, 10),
            manager=manager
        )
