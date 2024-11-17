from collections import defaultdict
import pygame
import pygame_gui
from scenes.scene import Scene
from scenes.events import RETURN_TO_SELECT_BATTLE
from ui_components.barracks_ui import UnitCount
from ui_components.tip_box import TipBox
from ui_components.save_battle_dialog import SaveBattleDialog
import battles

class BattleEditorScene(Scene):
    """Scene for editing and arranging battle levels."""
    
    def __init__(self, screen: pygame.Surface, manager: pygame_gui.UIManager) -> None:
        self.screen = screen
        self.manager = manager
        self.edit_buttons = {}
        screen.fill((0, 0, 0))
        self.create_ui()
    
    def create_ui(self, scroll_percentage: float = 0.0) -> None:
        padding = 5
        inner_padding = 5
        button_height = 30
        
        # Return button at top-left
        pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((padding, padding), (100, button_height)),
            text="Return",
            manager=self.manager
        )
        
        # Create scrollable container
        container_width = pygame.display.Info().current_w - 2 * padding
        container_height = pygame.display.Info().current_h - 45
        scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((padding, 40), (container_width, container_height)),
            manager=self.manager,
            allow_scroll_x=False,
        )

        # Calculate total height needed
        panel_height = 100
        total_height = len(battles.battles) * (panel_height + padding) + padding

        # Explicitly set scrollable area dimensions
        scroll_container.set_scrollable_area_dimensions((container_width - 20, total_height))

        # Create a panel inside the scroll container to hold all content
        content_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (container_width - 20, total_height)),
            manager=self.manager,
            container=scroll_container,
            object_id="#content_panel"
        )

        # Calculate space needed for 5 units plus padding
        unit_section_width = 5 * (UnitCount.size + inner_padding) + inner_padding

        # Add each battle's information
        for i, battle in enumerate(battles.battles):
            current_y = i * (panel_height + padding)
            
            # Create a container panel for this battle
            battle_panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect(
                    (padding, current_y),
                    (container_width - 40, panel_height)
                ),
                manager=self.manager,
                container=content_panel,
                object_id=f"#battle_panel_{i}"
            )
            
            panel_width = container_width - 40
            
            # Battle ID and Edit button side by side
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (inner_padding, inner_padding),
                    (unit_section_width - 50, 20)
                ),
                text=f"ID: {battle.id}",
                manager=self.manager,
                container=battle_panel
            )
            
            self.edit_buttons[battle.id] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (unit_section_width - 50, inner_padding),
                    (50, 20)
                ),
                text=f"Edit",
                manager=self.manager,
                container=battle_panel
            )
            
            # Enemy units (below battle ID)
            enemy_counts = defaultdict(int)
            for enemy_type, _ in battle.enemies:
                enemy_counts[enemy_type] += 1
            
            # Center the units vertically in the remaining space
            unit_section_height = panel_height - 20  # Space below the battle ID
            unit_y = 20 + (unit_section_height - UnitCount.size) // 2  # Center units in remaining space
            x = inner_padding
            
            # Display existing enemy units
            for unit_type, count in enemy_counts.items():
                UnitCount(
                    x_pos=x,
                    y_pos=unit_y,
                    unit_type=unit_type,
                    count=count,
                    interactive=False,
                    manager=self.manager,
                    container=battle_panel,
                    infinite=False,
                )
                x += UnitCount.size + inner_padding
            
            # Tips (right side) - adjusted to account for fixed unit section width
            tip_start_x = unit_section_width
            tip_width = 500
            tip_box = pygame_gui.elements.UITextBox(
                html_text='<br>'.join(battle.tip),
                relative_rect=pygame.Rect(
                    (tip_start_x, inner_padding),
                    (tip_width, panel_height - 2 * inner_padding)
                ),
                manager=self.manager,
                container=battle_panel
            )

        # Set scroll position
        scroll_container.vert_scroll_bar.start_percentage = scroll_percentage
    
    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle editor scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element.text == "Return":
                        pygame.event.post(pygame.event.Event(RETURN_TO_SELECT_BATTLE))
                    elif event.ui_element in self.edit_buttons.values():
                        battle_id = list(self.edit_buttons.keys())[list(self.edit_buttons.values()).index(event.ui_element)]
                        battle = battles.get_battle(battle_id)
                        
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            battle.enemies,
                            existing_battle=battle
                        )
                    elif hasattr(self, 'save_dialog'):
                        if event.ui_element == self.save_dialog.save_button:
                            # Find the scroll container and get current position
                            scroll_container = None
                            for element in self.manager.get_sprite_group():
                                if isinstance(element, pygame_gui.elements.UIScrollingContainer):
                                    scroll_container = element
                                    break
                            
                            scroll_percentage = 0.0
                            if scroll_container and scroll_container.vert_scroll_bar:
                                scroll_percentage = (scroll_container.vert_scroll_bar.scroll_position /
                                                  scroll_container.vert_scroll_bar.scrollable_height)
                            
                            self.save_dialog.save_battle()
                            self.save_dialog.kill()
                            self.save_dialog = None
                            
                            # Refresh UI with saved scroll position
                            self.manager.clear_and_reset()
                            self.create_ui(scroll_percentage)
                            
                        elif event.ui_element == self.save_dialog.cancel_button:
                            self.save_dialog.kill()
                            self.save_dialog = None
            
            self.manager.process_events(event)
        
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True