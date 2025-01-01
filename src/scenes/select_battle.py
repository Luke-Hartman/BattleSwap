from collections import defaultdict
import pygame
import battles
from camera import Camera
from scenes.scene import Scene
import pygame_gui
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scenes.events import SandboxSceneEvent, SetupBattleSceneEvent, TestEditorSceneEvent, MoveBattlesSceneEvent, CampaignSceneEvent
from progress_manager import ProgressManager
from world_map_view import WorldMapView
from ui_components.barracks_ui import BarracksUI, UnitCount
from components.unit_type import UnitType
from entities.units import unit_values

battle_swap_icon = pygame.image.load("assets/icons/BattleSwapIcon.png")

def calculate_net_value(solution_units: list[tuple[UnitType, tuple[int, int]]], enemy_units: list[tuple[UnitType, tuple[int, int]]]) -> int:
    """Calculate the net value difference between solution and enemy units."""
    solution_value = sum(unit_values[unit_type] for unit_type, _ in solution_units)
    enemy_value = sum(unit_values[unit_type] for unit_type, _ in enemy_units)
    return enemy_value - solution_value

class SelectBattleScene(Scene):
    """The scene for selecting a battle."""

    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager, progress_manager: ProgressManager):
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.progress_manager = progress_manager
        self.manager = manager
        self.create_buttons()

    def create_buttons(self) -> None:
        button_width = 200
        button_height = 64
        padding = 10
        icon_size = UnitCount.size
        
        title_width = 300
        title_height = 80
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w/2 - title_width/2, 0),
                (title_width, title_height)
            ),
            text="BattleSwap",
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )
        
        # Add sandbox and test editor buttons to the right side
        self.sandbox_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - button_width - padding, padding),
                (button_width, button_height)
            ),
            text="Sandbox Mode",
            manager=self.manager
        )
        
        self.test_editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 2 * button_width - 2 * padding, padding),
                (button_width, button_height)
            ),
            text="Test Editor",
            manager=self.manager
        )
        
        self.world_map_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 3 * button_width - 3 * padding, padding),
                (button_width, button_height)
            ),
            text="Move Battles",
            manager=self.manager
        )
        
        # Add campaign button to the right side
        self.campaign_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 4 * button_width - 4 * padding, padding),
                (button_width, button_height)
            ),
            text="Campaign",
            manager=self.manager
        )
        
        # Create scrollable container
        container_width = pygame.display.Info().current_w - 2 * padding
        container_height = pygame.display.Info().current_h - 225  # Leave space for other UI elements
        scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((padding, 100), (container_width, container_height)),
            manager=self.manager,
            allow_scroll_x=False,
        )

        # Calculate total height needed for content
        content_height = len(self.progress_manager.available_battles()) * (button_height + padding) + padding
        # Use max to ensure the container is at least as tall as its view area
        total_height = max(content_height, container_height)
        
        # Create a panel inside the scroll container to hold all content
        content_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (container_width, total_height)),
            manager=self.manager,
            container=scroll_container,
            object_id="#content_panel"
        )

        self.battle_buttons = []
        for i, hex_coords in enumerate(self.progress_manager.available_battles()):
            battle_id = next(battle.id for battle in battles.get_battles() if battle.hex_coords == hex_coords)
            y_pos = i * (button_height + padding) + padding
            x = pygame.display.Info().current_w // 2 - button_width // 2
            
            # Create battle button and store reference
            battle_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (x - padding, y_pos),
                    (button_width, button_height)
                ),
                text=battle_id,
                manager=self.manager,
                container=content_panel
            )
            self.battle_buttons.append(battle_button)
            
            x += button_width + padding
            solution = self.progress_manager.solutions.get(battle_id, None)
            
            # Show player's solution if it exists
            if solution is not None:
                unit_counts = defaultdict(int)
                for unit_type, _ in solution.unit_placements:
                    unit_counts[unit_type] += 1
                for unit_type, count in unit_counts.items():
                    UnitCount(
                        x_pos=x - padding,
                        y_pos=y_pos + button_height // 2 - icon_size // 2,
                        unit_type=unit_type,
                        count=count,
                        interactive=False,
                        manager=self.manager,
                        container=content_panel,
                        infinite=False,
                    )
                    x += icon_size + padding

            # Add swap icon and enemy units for both solved and unlocked battles
            swap_icon_size = 32
            pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    (x - padding, y_pos + button_height // 2 - swap_icon_size // 2),
                    (swap_icon_size, swap_icon_size)
                ),
                image_surface=battle_swap_icon,
                manager=self.manager,
                container=content_panel
            )
            x += swap_icon_size + padding

            # Add enemy unit counts
            enemy_counts = defaultdict(int)
            for enemy_type, _ in battles.get_battle_id(battle_id).enemies:
                enemy_counts[enemy_type] += 1
            for unit_type, count in enemy_counts.items():
                UnitCount(
                    x_pos=x - padding,
                    y_pos=y_pos + button_height // 2 - icon_size // 2,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager,
                    container=content_panel,
                    infinite=False,
                )
                x += icon_size + padding

            # Calculate and display net value
            if solution is not None:
                net_value = calculate_net_value(solution.unit_placements, battles.get_battle_id(battle_id).enemies)
                value_object_id = (
                    "#positive_value" if net_value > 0 
                    else "#neutral_value" if net_value == 0 
                    else "#negative_value"
                )
                pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(
                        (x - padding, y_pos + button_height // 2 - 10),
                        (50, 20)
                    ),
                    text=f"{net_value:+}",
                    manager=self.manager,
                    container=content_panel,
                    object_id=pygame_gui.core.ObjectID(
                        class_id="@value_label",
                        object_id=value_object_id
                    )
                )
                x += 50 + padding

        # Create barracks only if there are completed battles
        if self.progress_manager.solutions:
            self.barracks = BarracksUI(
                self.manager,
                self.progress_manager.available_units(None),
                interactive=False,
                sandbox_mode=False,
            )
        else:
            self.barracks = None

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the select battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.sandbox_button:
                        # Create the battle object for the sandbox
                        battle = battles.Battle(
                            id="sandbox",
                            tip=["A customizable battle for experimenting"],
                            hex_coords=(0, 0),  # Place at origin of hex grid
                            allies=[],
                            enemies=[],
                            is_test=False,
                        )

                        # Create WorldMapView with just the sandbox battle
                        camera = Camera()
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=[battle],
                            camera=camera
                        )
                        pygame.event.post(SandboxSceneEvent(
                            world_map_view=world_map_view,
                            battle_id=battle.id,
                            sandbox_mode=True,
                        ).to_event())
                    elif event.ui_element == self.test_editor_button:
                        pygame.event.post(TestEditorSceneEvent().to_event())
                    elif event.ui_element == self.world_map_button:
                        camera = Camera(zoom=1/2)
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=battles.get_battles(),
                            camera=camera
                        )
                        pygame.event.post(MoveBattlesSceneEvent(
                            world_map_view=world_map_view,
                        ).to_event())
                    elif event.ui_element == self.campaign_button:
                        camera = Camera(zoom=1/2)
                        world_map_view = WorldMapView(
                            screen=self.screen,
                            manager=self.manager,
                            battles=self.progress_manager.get_battles_including_solutions(),
                            camera=camera
                        )
                        pygame.event.post(CampaignSceneEvent(
                            world_map_view=world_map_view,
                        ).to_event())
                    elif event.ui_element in self.battle_buttons:
                        battle_id = event.ui_element.text
                        solution = self.progress_manager.solutions.get(battle_id, None)
                        ally_placements = solution.unit_placements if solution else []
                        pygame.event.post(
                            SetupBattleSceneEvent(
                                battle_id=battle_id,
                                ally_placements=ally_placements,
                                play_tip_sound=True if solution is None else False
                            ).to_event()
                        )
        
            self.manager.process_events(event)

        self.manager.update(time_delta)
        self.screen.fill((0, 0, 0))
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)
