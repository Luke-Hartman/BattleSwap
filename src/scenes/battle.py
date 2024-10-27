import esper
import pygame
import pygame_gui
from processors.collision_processor import CollisionProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from processors.animation_processor import AnimationProcessor
from processors.movement_processor import MovementProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.targeting_processor import TargetingProcessor
from scenes.scene import Scene
from scenes.events import RETURN_TO_SELECT_BATTLE
from CONSTANTS import SCREEN_WIDTH, SCREEN_HEIGHT
from camera import Camera

class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera
        self.manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        movement_processor = MovementProcessor()
        pursuing_processor = PursuingProcessor()
        targeting_processor = TargetingProcessor()
        collision_processor = CollisionProcessor()
        esper.add_processor(pursuing_processor)
        esper.add_processor(movement_processor)
        esper.add_processor(collision_processor)
        esper.add_processor(targeting_processor)
        self.create_return_button()

    def create_return_button(self) -> None:
        button_width = 100
        button_height = 30
        button_rect = pygame.Rect(
            (10, 10),
            (button_width, button_height)
        )
        self.return_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text="Return",
            manager=self.manager
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(pygame.event.Event(RETURN_TO_SELECT_BATTLE))
                        esper.clear_database()
                        esper.remove_processor(RenderingProcessor)
                        esper.remove_processor(AnimationProcessor)
                        esper.remove_processor(PursuingProcessor)
                        esper.remove_processor(MovementProcessor)
                        esper.remove_processor(CollisionProcessor)
                        esper.remove_processor(TargetingProcessor)
                        return True
            
            self.manager.process_events(event)

        self.camera.handle_event(events)
        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        
        return True
