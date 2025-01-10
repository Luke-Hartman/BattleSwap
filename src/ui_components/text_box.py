import pygame
import pygame_gui
from pygame_gui.elements import UIPanel, UILabel


class TextBox(UIPanel):
    def __init__(
        self,
        strings: list[str],
        top_center_pos: tuple[int, int],
        manager: pygame_gui.UIManager,
        container: UIPanel = None
    ):
        # Create with temporary dimensions that will be updated
        super().__init__(
            relative_rect=pygame.Rect(0, 0, -1, -1),
            manager=manager,
            container=container
        )

        margin = 5
        padding = 1
        # First pass: create labels to measure max width
        self.labels = []
        max_label_width = 0
        total_label_height = 2 * margin

        for text in strings:
            label = UILabel(
                relative_rect=pygame.Rect(0, 0, -1, -1),
                text=text,
                manager=self.ui_manager,
                container=self,
                object_id='#tip_box'
            )
            self.labels.append(label)
            label.rebuild()  # Force UI to compute size
            if label.rect.width > max_label_width:
                max_label_width = label.rect.width + 2 * padding + 2 * margin
            total_label_height += label.rect.height + padding

        # Resize panel to match widest label and total stacked height
        self.set_dimensions((max_label_width, total_label_height))

        # Position the panel so its top-center is at top_center_pos
        self.set_position((
            top_center_pos[0] - (max_label_width // 2),
            top_center_pos[1]
        ))

        # Second pass: position each label in the panel
        current_y = margin
        for label in self.labels:
            # Center each label horizontally
            label.set_relative_position((
                padding + (max_label_width - 2*padding - label.rect.width) // 2,
                current_y
            ))
            current_y += label.rect.height + padding
