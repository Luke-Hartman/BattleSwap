"""Main module for the Battle Swap game."""

import esper
import pygame
import os
from components.position import Position
from components.velocity import Velocity
from components.renderable import Renderable
from components.animation import Animation
from components.health import Health
from components.team import Team, TeamType
from processors.movement_processor import MovementProcessor
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FRAME_RATE = 60

def load_sprite_sheet(filename):
    """Load a sprite sheet from the assets directory.

    Args:
        filename (str): The name of the sprite sheet file.

    Returns:
        pygame.Surface: The loaded sprite sheet surface.
    """
    return pygame.image.load(os.path.join("assets", "MinifolksHumans", "Without Outline", filename)).convert_alpha()

def main():
    """Initialize the game and run the main game loop."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Battle Swap")

    swordsman_sheet = load_sprite_sheet("MiniSwordMan.png")
    archer_sheet = load_sprite_sheet("MiniArcherMan.png")

    # Create an ally swordsman entity
    esper.create_entity(
        Position(400, 300),
        Velocity(1, 0),
        Renderable(swordsman_sheet, 32, 32, scale=4),
        Animation(row=1, frame_count=6, frame_duration=6),
        Health(100),
        Team(TeamType.ALLY)
    )

    # Create an enemy archer entity
    esper.create_entity(
        Position(200, 300),
        Velocity(-1, 0),
        Renderable(archer_sheet, 32, 32, scale=4),
        Animation(row=1, frame_count=6, frame_duration=6),
        Health(100),
        Team(TeamType.ENEMY)
    )

    esper.add_processor(MovementProcessor(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT))
    esper.add_processor(AnimationProcessor())
    esper.add_processor(RenderingProcessor(screen))

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((34, 139, 34))
        esper.process()
        pygame.display.flip()
        clock.tick(FRAME_RATE)

    pygame.quit()

if __name__ == "__main__":
    main()