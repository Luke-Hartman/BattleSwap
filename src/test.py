"""Basic PyGame GUI test module demonstrating a simple button interface."""

import pygame
import pygame_gui
from typing import Optional

class TestGui:
    def __init__(self) -> None:
        pygame.init()
        
        self.window_size = (800, 600)
        self.window_surface = pygame.display.set_mode(self.window_size)
        
        self.background = pygame.Surface(self.window_size)
        self.background.fill(pygame.Color('#000000'))
        
        self.manager = pygame_gui.UIManager(self.window_size)
        
        # Create a square button (100x100 pixels) centered horizontally, 
        # positioned 200 pixels from the top
        button_width = 100
        button_x = (self.window_size[0] - button_width) // 2
        
        # Create a panel that will contain the button
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((button_x, 200), (button_width, button_width)),
            manager=self.manager,
            margins={'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        )
        
        # Create the button inside the panel
        self.test_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (button_width, button_width)),
            text='Click Me!',
            manager=self.manager,
            container=self.panel
        )
        
        # Add a label overlapping the bottom of the button
        self.label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, button_width - 25), (button_width, 20)),
            text="Overlay Text",
            manager=self.manager,
            container=self.panel
        )
        
        self.clock = pygame.time.Clock()
        self.is_running = True

    def run(self) -> None:
        while self.is_running:
            time_delta = self.clock.tick(60)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.test_button:
                        print("Button pressed!")

                self.manager.process_events(event)

            self.manager.update(time_delta)

            self.window_surface.blit(self.background, (0, 0))
            self.manager.draw_ui(self.window_surface)

            pygame.display.update()

if __name__ == '__main__':
    app = TestGui()
    app.run()
