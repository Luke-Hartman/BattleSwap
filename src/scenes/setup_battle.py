"""Setup battle scene for Battle Swap."""

from typing import Tuple
import esper
import pygame
import pygame_gui
from battles import battles
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from processors.animation_processor import AnimationProcessor
from processors.rendering_processor import RenderingProcessor
from scenes.scene import Scene
from scenes.events import START_BATTLE
from CONSTANTS import SCREEN_WIDTH, SCREEN_HEIGHT, NO_MANS_LAND_WIDTH

class SetupBattleScene(Scene):
    """The scene for setting up the battle."""

    def __init__(self, screen: pygame.Surface, battle: str):
        self.screen = screen
        self.battle = battle
        self.manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.selected_entity = None
        
        self.rendering_processor = RenderingProcessor(screen)
        esper.add_processor(self.rendering_processor)
        animation_processor = AnimationProcessor()
        esper.add_processor(animation_processor)
        # Create the battle entities
        battles[battle]()

        self.create_start_button()

    def create_start_button(self) -> None:
        """Create the start battle button."""
        button_width = 200
        button_height = 50
        button_rect = pygame.Rect(
            (SCREEN_WIDTH - button_width - 10, SCREEN_HEIGHT - button_height - 10),
            (button_width, button_height)
        )
        self.start_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text="Start Battle",
            manager=self.manager
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """
        Update the setup battle scene.

        Args:
            time_delta: Time passed since last frame.
            events: List of pygame events.

        Returns:
            bool: True if the game should continue, False if it should quit.
        """
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.start_button:
                        pygame.event.post(pygame.event.Event(START_BATTLE, battle=self.battle))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.selected_entity is None:
                    self.select_unit(mouse_pos)
                else:
                    self.selected_entity = None
            if self.selected_entity is not None and event.type == pygame.MOUSEMOTION:
                pos = esper.component_for_entity(self.selected_entity, Position)
                x, y = event.pos
                x = min(x, SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2)
                pos.x, pos.y = x, y
            self.manager.process_events(event)

        self.screen.fill((34, 100, 34))
        # Draw vertical lines to represent no man's land
        pygame.draw.line(self.screen, (0, 0, 0), (SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2, 0), (SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2, SCREEN_HEIGHT), 2)
        pygame.draw.line(self.screen, (0, 0, 0), (SCREEN_WIDTH // 2 + NO_MANS_LAND_WIDTH//2, 0), (SCREEN_WIDTH // 2 + NO_MANS_LAND_WIDTH//2, SCREEN_HEIGHT), 2)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        
        return True

    def select_unit(self, mouse_pos: Tuple[int, int]) -> None:
        """Select a unit at the given mouse position."""
        for ent, (team, sprite) in esper.get_components(Team, SpriteSheet):
            if team.type == TeamType.TEAM1 and sprite.rect.collidepoint(mouse_pos):
                self.selected_entity = ent
                break

    def move_unit(self, mouse_pos: Tuple[int, int]) -> None:
        """Move the selected unit to the given mouse position."""
        if self.selected_entity is not None:
            pos = esper.component_for_entity(self.selected_entity, Position)
            pos.x, pos.y = mouse_pos
            self.selected_entity = None
