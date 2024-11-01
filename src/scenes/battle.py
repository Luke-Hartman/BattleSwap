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
from scenes.events import RETURN_TO_SELECT_BATTLE, SETUP_BATTLE_SCENE
from CONSTANTS import SCREEN_WIDTH, SCREEN_HEIGHT
from camera import Camera
from ui_components.return_button import ReturnButton
from progress_manager import ProgressManager, Solution
from components.unit_state import State, UnitState
from components.team import Team, TeamType

class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(self, screen: pygame.Surface, camera: Camera, progress_manager: ProgressManager, potential_solution: Solution):
        self.screen = screen
        self.progress_manager = progress_manager
        self.potential_solution = potential_solution
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
        self.return_button = ReturnButton(self.manager)
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH - 210, 10), (100, 30)),
            text='Restart',
            manager=self.manager
        )
        self.victory_button = None
        self.victory_achieved = False
        

    def check_victory(self) -> None:
        """Check if all enemy units are defeated and show victory button if they are."""
        if self.victory_achieved:
            return

        # Check if any enemies are still alive
        for ent, (unit_state, team) in esper.get_components(UnitState, Team):
            if team.type == TeamType.TEAM1:
                continue
            if unit_state.state != State.DEAD:
                return

        # If we get here, all enemies are dead
        self.victory_achieved = True
        self.victory_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 75), (200, 50)),
            text='Victory!',
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
                        self._cleanup()
                        pygame.event.post(pygame.event.Event(RETURN_TO_SELECT_BATTLE))
                        return True
                    elif event.ui_element == self.victory_button:
                        self.progress_manager.save_solution(self.potential_solution)
                        self._cleanup()
                        pygame.event.post(pygame.event.Event(RETURN_TO_SELECT_BATTLE))
                        return True
                    elif event.ui_element == self.restart_button:
                        self._cleanup()
                        pygame.event.post(pygame.event.Event(SETUP_BATTLE_SCENE, battle=self.potential_solution.battle_id, potential_solution=self.potential_solution))
                        return True
            
            self.manager.process_events(event)

        self.check_victory()
        self.camera.handle_event(events)
        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        
        return True

    def _cleanup(self) -> None:
        """Clean up processors and entity database."""
        esper.clear_database()
        esper.remove_processor(RenderingProcessor)
        esper.remove_processor(AnimationProcessor)
        esper.remove_processor(PursuingProcessor)
        esper.remove_processor(MovementProcessor)
        esper.remove_processor(CollisionProcessor)
        esper.remove_processor(TargetingProcessor)
        
