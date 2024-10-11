"""Rendering processor for the Battle Swap game."""

import pygame
import esper
from components.position import Position
from components.renderable import Renderable
from components.animation import Animation
from components.team import Team, TeamType

class RenderingProcessor(esper.Processor):
    """Processor responsible for rendering entities."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the RenderingProcessor.

        Args:
            screen: The screen surface to draw on.
        """
        super().__init__()
        self.screen = screen

    def process(self):
        """Render all entities with a Position component."""
        for ent, (pos, rend, anim, team) in esper.get_components(Position, Renderable, Animation, Team):
            frame = rend.animation_frames[anim.row][anim.current_frame]
            if team.team_type == TeamType.ENEMY:
                frame = pygame.transform.flip(frame, True, False)
            self.screen.blit(frame, (int(pos.x - rend.frame_width * rend.scale // 2), int(pos.y - rend.frame_height * rend.scale // 2)))