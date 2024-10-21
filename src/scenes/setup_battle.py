"""Setup battle scene for Battle Swap."""

from typing import Tuple, Optional
from dataclasses import dataclass
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

@dataclass
class SelectedUnit:
    """Dataclass to store information about the selected unit."""
    entity: int
    original_pos: Tuple[float, float]

class SetupBattleScene(Scene):
    """The scene for setting up the battle."""

    def __init__(self, screen: pygame.Surface, battle: str):
        self.screen = screen
        self.battle = battle
        self.manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.selected_unit: Optional[SelectedUnit] = None
        
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if self.selected_unit is None:
                        self.select_unit(mouse_pos)
                    else:
                        self.place_selected_unit(mouse_pos)
                elif event.button == 3:  # Right click
                    self.deselect_unit()
            if self.selected_unit is not None and event.type == pygame.MOUSEMOTION:
                pos = esper.component_for_entity(self.selected_unit.entity, Position)
                x, y = event.pos
                x = min(x, SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2)
                pos.x, pos.y = x, y
            self.manager.process_events(event)

        self.screen.fill((34, 100, 34))
        # Draw vertical lines to represent no man's land
        pygame.draw.line(self.screen, (0, 0, 0), (SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2, 0), (SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2, SCREEN_HEIGHT), 2)
        pygame.draw.line(self.screen, (0, 0, 0), (SCREEN_WIDTH // 2 + NO_MANS_LAND_WIDTH//2, 0), (SCREEN_WIDTH // 2 + NO_MANS_LAND_WIDTH//2, SCREEN_HEIGHT), 2)
        # Draw a circle where the selected unit was
        if self.selected_unit is not None:
            pygame.draw.circle(self.screen, (0, 200, 0), self.selected_unit.original_pos, 3)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        
        return True

    def select_unit(self, mouse_pos: Tuple[int, int]) -> None:
        """Select a unit at the given mouse position."""
        candidate_unit = SelectedUnit(None, (0, -float('inf')))
        for ent, (team, sprite, pos) in esper.get_components(Team, SpriteSheet, Position):
            if team.type == TeamType.TEAM1 and sprite.rect.collidepoint(mouse_pos):
                relative_mouse_pos = (mouse_pos[0] - sprite.rect.x, mouse_pos[1] - sprite.rect.y)
                try:
                    if sprite.image.get_at(relative_mouse_pos).a != 0:
                        if pos.y > candidate_unit.original_pos[1]:
                            candidate_unit = SelectedUnit(ent, (pos.x, pos.y))
                except IndexError:
                    pass
        if candidate_unit.entity is not None:
            self.selected_unit = candidate_unit

    def place_selected_unit(self, mouse_pos: Tuple[int, int]) -> None:
        """Place the selected unit at the given mouse position."""
        if self.selected_unit is not None:
            pos = esper.component_for_entity(self.selected_unit.entity, Position)
            x, y = mouse_pos
            x = min(x, SCREEN_WIDTH // 2 - NO_MANS_LAND_WIDTH//2)
            pos.x, pos.y = x, y
            self.selected_unit = None

    def deselect_unit(self) -> None:
        """Deselect the current unit and return it to its original position."""
        if self.selected_unit is not None:
            pos = esper.component_for_entity(self.selected_unit.entity, Position)
            pos.x, pos.y = self.selected_unit.original_pos
            self.selected_unit = None
