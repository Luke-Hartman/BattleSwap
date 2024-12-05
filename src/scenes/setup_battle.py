"""Setup battle scene for Battle Swap."""
from typing import List, Tuple, Optional
import esper
import pygame
import pygame_gui
from auto_battle import get_unit_placements
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_type import UnitType, UnitTypeComponent
from events import emit_event, CHANGE_MUSIC, ChangeMusicEvent, PLAY_VOICE, PlayVoiceEvent
from processors.animation_processor import AnimationProcessor
from processors.orientation_processor import OrientationProcessor
from processors.position_processor import PositionProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from processors.rotation_processor import RotationProcessor
from scenes.scene import Scene
from scenes.events import BattleSceneEvent, PreviousSceneEvent
from game_constants import gc
from camera import Camera
from entities.units import TeamType, create_unit
from battles import get_battle
from ui_components.start_button import StartButton
from ui_components.return_button import ReturnButton
from ui_components.barracks_ui import BarracksUI, UnitCount
from progress_manager import ProgressManager
from ui_components.tip_box import TipBox
from ui_components.reload_constants_button import ReloadConstantsButton
from components.range_indicator import RangeIndicator
from components.stats_card import StatsCard
from voice import play_intro


class SetupBattleScene(Scene):
    """The scene for setting up the battle.
    
    This scene allows players to position their units on the battlefield before the battle begins.
    It provides a UI for selecting units from the barracks and placing them on the field.
    """

    def __init__(
            self,
            screen: pygame.Surface,
            camera: Camera,
            manager: pygame_gui.UIManager,
            battle_id: str,
            progress_manager: ProgressManager,
            ally_placements: List[Tuple[UnitType, Tuple[int, int]]],
            play_tip_sound: bool,
    ):
        """Initialize the setup battle scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view of the battlefield.
            manager: The pygame_gui manager for the scene.
            battle_id: The name of the battle to set up.
            progress_manager: The progress manager for the game.
            ally_placements: List of starting ally placements.
            play_tip_sound: Whether to play the tip sound.  
        """
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.progress_manager = progress_manager
        self.camera = camera
        self.battle = get_battle(battle_id)
        self.manager = manager
        self.selected_unit_id: Optional[int] = None

        # Center the camera on the battlefield
        self.camera.x = (gc.BATTLEFIELD_WIDTH - pygame.display.Info().current_w) // 2
        self.camera.y = (gc.BATTLEFIELD_HEIGHT - pygame.display.Info().current_h) // 2
        
        self.return_button = ReturnButton(self.manager)
        
        esper.add_processor(RenderingProcessor(screen, self.camera, self.manager))
        esper.add_processor(AnimationProcessor())
        esper.add_processor(PositionProcessor())
        esper.add_processor(OrientationProcessor())
        esper.add_processor(RotationProcessor())

        self.barracks = BarracksUI(
            self.manager,
            self.progress_manager.available_units(current_battle_id=battle_id),
            interactive=True,
            sandbox_mode=False,
        )
        self.start_button = StartButton(self.manager)
        for (unit_type, position) in ally_placements:
            create_unit(position[0], position[1], unit_type, TeamType.TEAM1)
            self.barracks.remove_unit(unit_type)

        for unit_type, position in self.battle.enemies:
            create_unit(position[0], position[1], unit_type, TeamType.TEAM2)

        
        self.tip_box = TipBox(self.manager, self.battle)
        self.reload_constants_button = ReloadConstantsButton(self.manager)
        if self.battle.tip_voice_filename is not None and play_tip_sound:
            emit_event(PLAY_VOICE, event=PlayVoiceEvent(
                filename=self.battle.tip_voice_filename,
                force=True,
            ))

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the setup battle scene.

        Handles user input, updates unit positions, and renders the scene.

        Args:
            time_delta: Time passed since last frame in seconds.
            events: List of pygame events to process.

        Returns:
            bool: True if the game should continue, False if it should quit.
        """
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.start_button:
                        if self.selected_unit_id is not None:
                            self.return_unit_to_barracks(self.selected_unit_id)
                            self.selected_unit_id = None
                        ally_placements = get_unit_placements(TeamType.TEAM1)
                        pygame.event.post(BattleSceneEvent(
                            ally_placements=ally_placements,
                            enemy_placements=self.battle.enemies,
                            battle_id=self.battle.id,
                            sandbox_mode=False,
                            editor_scroll=None,
                        ).to_event())
                    elif event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)
                    elif isinstance(event.ui_element, UnitCount):
                        play_intro(event.ui_element.unit_type)
                        self.create_unit_from_list(event.ui_element)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if self.selected_unit_id is None:
                        self.selected_unit_id = self.get_hovered_unit(mouse_pos)
                    else:
                        # Mouse must be within 25 pixels of the legal placement area to place the unit
                        grace_zone = 25
                        pos = esper.component_for_entity(self.selected_unit_id, Position)
                        adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
                        distance = ((adjusted_mouse_pos[0] - pos.x)**2 + (adjusted_mouse_pos[1] - pos.y)**2)**0.5
                        if distance <= grace_zone:
                            self.place_unit()
                elif event.button == 3:  # Right click
                    if self.selected_unit_id is not None:
                        self.return_unit_to_barracks(self.selected_unit_id)
                    else:
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_on_unit = self.get_hovered_unit(mouse_pos)
                        if clicked_on_unit is not None:
                            self.return_unit_to_barracks(clicked_on_unit)
            self.reload_constants_button.handle_event(event)
            self.manager.process_events(event)

        if self.selected_unit_id is not None:
            pos = esper.component_for_entity(self.selected_unit_id, Position)
            mouse_pos = pygame.mouse.get_pos()
            adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
            x, y = adjusted_mouse_pos
            x = max(0, min(x, gc.BATTLEFIELD_WIDTH // 2 - gc.NO_MANS_LAND_WIDTH//2))
            y = max(0, min(y, gc.BATTLEFIELD_HEIGHT))

            # Snap to grid if shift is held
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                x = round(x / gc.GRID_SIZE) * gc.GRID_SIZE
                y = round(y / gc.GRID_SIZE) * gc.GRID_SIZE

            pos.x, pos.y = x, y
            range_indicator = esper.try_component(self.selected_unit_id, RangeIndicator)
            if range_indicator is not None:
                range_indicator.enabled = True

        # Update stats card for hovered unit
        mouse_pos = pygame.mouse.get_pos()
        hovered_unit = self.get_hovered_unit(mouse_pos)
        if hovered_unit is not None:
            stats_card = esper.component_for_entity(hovered_unit, StatsCard)
            stats_card.active = True

        self.camera.update(time_delta)

        self.screen.fill((0, 0, 0))
        keys = pygame.key.get_pressed()
        show_grid = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True, show_grid=show_grid)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)

    def place_unit(self) -> None:
        """Place the currently selected unit on the battlefield."""
        assert self.selected_unit_id is not None
        unit_type = esper.component_for_entity(self.selected_unit_id, UnitTypeComponent).type
        range_indicator = esper.try_component(self.selected_unit_id, RangeIndicator)
        if range_indicator is not None:
            range_indicator.enabled = False
        # if there are more available, continue to place them
        if self.barracks.units[unit_type] > 0:
            entity = create_unit(0, 0, unit_type, TeamType.TEAM1)
            self.barracks.remove_unit(unit_type)
            self.selected_unit_id = entity
        else:
            self.selected_unit_id = None

    def return_unit_to_barracks(self, unit_id: int) -> None:
        """Deselect the current unit and return it to the unit pool."""
        unit_type = esper.component_for_entity(unit_id, UnitTypeComponent).type
        esper.delete_entity(unit_id, immediate=True)
        self.barracks.add_unit(unit_type)
        self.selected_unit_id = None

    def create_unit_from_list(self, unit_list_item: UnitCount) -> None:
        """Create a unit from a unit list item and update the UI."""
        entity = create_unit(0, 0, unit_list_item.unit_type, TeamType.TEAM1)
        self.barracks.remove_unit(unit_list_item.unit_type)
        self.selected_unit_id = entity

    def get_hovered_unit(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Return the unit at the given mouse position, for hover effects.
        
        Args:
            mouse_pos: The (x, y) screen coordinates of the mouse.
            
        Returns:
            Optional[int]: The entity ID of the hovered unit, or None if no unit is hovered.
        """
        adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
        candidate_unit_id = None
        highest_y = -float('inf')
        for ent, (team, sprite, pos) in esper.get_components(Team, SpriteSheet, Position):
            if sprite.rect.collidepoint(adjusted_mouse_pos):
                relative_mouse_pos = (
                    adjusted_mouse_pos[0] - sprite.rect.x,
                    adjusted_mouse_pos[1] - sprite.rect.y
                )
                try:
                    if sprite.image.get_at(relative_mouse_pos).a != 0:
                        if pos.y > highest_y:
                            highest_y = pos.y
                            candidate_unit_id = ent
                except IndexError:
                    pass
        return candidate_unit_id
