"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import argparse
import pygame
from entities.units import load_sprite_sheets
from handlers.combat_handler import CombatHandler
from handlers.sound_handler import SoundHandler
from handlers.state_machine import StateMachine
from scenes.scene_manager import SceneManager
from time_manager import time_manager
from visuals import load_visual_sheets
from game_constants import gc
import steam

# Initialize Pygame
pygame.init()

# Initialize Steamworks
steam.init_steam()

# Set up the display
# Use the full screen

# This is slightly awkward, but it let's us
# 1. Get the correct screen size
# 2. Use the "SCALED" flag, which is apparently required for the steam overlay
screen = pygame.display.set_mode((0, 0),pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
screen = pygame.display.set_mode(
    (screen_width, screen_height),
    pygame.SCALED | pygame.FULLSCREEN
)
pygame.display.set_caption("Battle Swap")

# Initialize font for FPS counter
fps_font = pygame.font.SysFont('Arial', 30)

# Load sprite sheets
load_sprite_sheets()
load_visual_sheets()

combat_handler = CombatHandler()
state_machine = StateMachine()
sound_handler = SoundHandler()

# Main game loop
running = True
clock = pygame.time.Clock()

parser = argparse.ArgumentParser()
parser.add_argument("--no_dev", action="store_true", default=False)
args = parser.parse_args()

scene_manager = SceneManager(
    screen,
    developer_mode=not args.no_dev
)

while running:
    dt = clock.tick(time_manager.max_fps) / 1000
    events = pygame.event.get()

    running = scene_manager.update(dt, events)
    
    # # Render FPS counter
    # fps_text = fps_font.render(f'FPS: {int(clock.get_fps())}', True, (255, 255, 255))
    # fps_rect = fps_text.get_rect(topright=(screen.get_width() - 10, 10))
    # screen.blit(fps_text, fps_rect)
    
    pygame.display.flip()

pygame.quit()
