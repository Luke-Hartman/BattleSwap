from typing import List, Tuple, Optional
import esper
import pygame
import pygame_gui
from battles import get_battle
from components.unit_type import UnitType
from entities.units import create_unit
from processors.ability_processor import AbilityProcessor
from processors.attached_processor import AttachedProcessor
from processors.aura_processor import AuraProcessor
from processors.collision_processor import CollisionProcessor
from processors.dead_processor import DeadProcessor
from processors.expiration_processor import ExpirationProcessor
from processors.fleeing_processor import FleeingProcessor
from processors.idle_processor import IdleProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from processors.animation_processor import AnimationProcessor
from processors.movement_processor import MovementProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.status_effect_processor import StatusEffectProcessor
from processors.targetting_processor import TargettingProcessor
from processors.unique_processor import UniqueProcessor
from scenes.scene import Scene
from scenes.events import SandboxSceneEvent, SelectBattleSceneEvent, SetupBattleSceneEvent
from camera import Camera
from ui_components.return_button import ReturnButton
from progress_manager import ProgressManager, Solution
from components.unit_state import State, UnitState
from components.team import Team, TeamType

class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
        manager: pygame_gui.UIManager,
        progress_manager: ProgressManager,
        ally_placements: List[Tuple[UnitType, Tuple[int, int]]],
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        battle_id: Optional[str] = None,
        sandbox_mode: bool = False,
        editor_scroll: float = 0.0
    ):
        """Initialize the battle scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view.
            manager: The pygame_gui UI manager.
            progress_manager: The progress manager.
            ally_placements: The placements of the ally units.
            enemy_placements: The placements of the enemy units.
            battle_id: The id of the battle to load.
            sandbox_mode: Whether this battle is in sandbox mode.
            editor_scroll: The scroll position of the battle editor.
        """
        self.screen = screen
        self.camera = camera
        self.manager = manager
        self.progress_manager = progress_manager
        self.ally_placements = ally_placements
        self.enemy_placements = enemy_placements
        self.battle_id = battle_id
        self.sandbox_mode = sandbox_mode
        self.editor_scroll = editor_scroll
        for unit_type, position in self.ally_placements:
            create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM1)
        for unit_type, position in self.enemy_placements:
            create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM2)
        unique_processor = UniqueProcessor()
        targetting_processor = TargettingProcessor()
        idle_processor = IdleProcessor()
        fleeing_processor = FleeingProcessor()
        ability_processor = AbilityProcessor()
        dead_processor = DeadProcessor()
        aura_processor = AuraProcessor()
        movement_processor = MovementProcessor()
        pursuing_processor = PursuingProcessor()
        collision_processor = CollisionProcessor()
        attached_processor = AttachedProcessor()
        expiration_processor = ExpirationProcessor()
        status_effect_processor = StatusEffectProcessor()
        animation_processor = AnimationProcessor()
        rendering_processor = RenderingProcessor(
            screen=self.screen,
            camera=self.camera
        )
        esper.add_processor(unique_processor)
        esper.add_processor(targetting_processor)
        esper.add_processor(idle_processor)
        esper.add_processor(fleeing_processor)
        esper.add_processor(ability_processor)
        esper.add_processor(pursuing_processor)
        esper.add_processor(dead_processor)
        esper.add_processor(aura_processor)
        esper.add_processor(movement_processor)
        esper.add_processor(collision_processor)
        esper.add_processor(attached_processor)
        esper.add_processor(expiration_processor)
        esper.add_processor(status_effect_processor)
        esper.add_processor(animation_processor)
        esper.add_processor(rendering_processor)
        self.return_button = ReturnButton(self.manager)
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((pygame.display.Info().current_w - 210, 10), (100, 30)),
            text='Restart',
            manager=self.manager
        )
        self.victory_button = None
        self.victory_achieved = False
        

    def check_victory(self) -> None:
        """Check if all enemy units are defeated and show victory button if they are."""
        if self.sandbox_mode or self.victory_achieved:
            return

        # Only check for victory in normal mode
        for ent, (unit_state, team) in esper.get_components(UnitState, Team):
            if team.type == TeamType.TEAM1:
                continue
            if unit_state.state != State.DEAD:
                return

        # If we get here, all enemies are dead
        self.victory_achieved = True
        self.victory_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((pygame.display.Info().current_w//2 - 100, pygame.display.Info().current_h - 75), (200, 50)),
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
                        pygame.event.post(SelectBattleSceneEvent().to_event())
                        return True
                    elif event.ui_element == self.victory_button:
                        self.progress_manager.save_solution(Solution(self.battle_id, self.ally_placements))
                        pygame.event.post(SelectBattleSceneEvent().to_event())
                        return True
                    elif event.ui_element == self.restart_button:
                        if self.sandbox_mode:
                            pygame.event.post(
                                SandboxSceneEvent(
                                    ally_placements=self.ally_placements,
                                    enemy_placements=self.enemy_placements,
                                    battle_id=self.battle_id,
                                    editor_scroll=self.editor_scroll
                                ).to_event()
                            )
                        else:
                            pygame.event.post(
                                SetupBattleSceneEvent(
                                    ally_placements=self.ally_placements,
                                    enemy_placements=self.enemy_placements,
                                    battle_id=self.battle_id
                                ).to_event()
                            )
                        return True
            
            self.manager.process_events(event)

        self.check_victory()
        self.camera.update(time_delta)
        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True
