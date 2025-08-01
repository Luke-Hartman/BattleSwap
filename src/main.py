"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import argparse
import sys
import pygame
import OpenGL.GL as gl
from entities.units import load_sprite_sheets
from handlers.combat_handler import CombatHandler
from handlers.sound_handler import SoundHandler
from handlers.state_machine import StateMachine
from scenes.scene_manager import scene_manager
from selected_unit_manager import selected_unit_manager
import timing
from visuals import load_visual_sheets
from info_mode_manager import info_mode_manager
#import steam

# Initialize Pygame
pygame.init()

# Initialize Steamworks
#steam.init_steam()

# Set up the display with OpenGL
# Use the same approach as original but with OpenGL flags
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
screen = pygame.display.set_mode(
    (screen_width, screen_height),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
)
pygame.display.set_caption("Battle Swap")

# Set up OpenGL
from game_constants import gc
# Convert RGB [0-255] to OpenGL [0.0-1.0] format
bg_r, bg_g, bg_b = gc.MAP_BACKGROUND_COLOR
gl.glClearColor(bg_r / 255.0, bg_g / 255.0, bg_b / 255.0, 1)
gl.glMatrixMode(gl.GL_PROJECTION)
gl.glLoadIdentity()
gl.glOrtho(0, screen_width, screen_height, 0, -1, 1)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

# Create off-screen surface for game rendering
game_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

# Dirty flag to track when content has been drawn to the surface
surface_dirty = False

def mark_surface_dirty():
    """Mark the game surface as dirty (content has been drawn to it)."""
    global surface_dirty
    surface_dirty = True

def surface_to_texture(surface):
    """Convert pygame surface to OpenGL texture."""
    texture_data = pygame.image.tobytes(surface, 'RGBA', False)
    texture_id = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, surface.get_width(), surface.get_height(), 
                    0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    return texture_id

def draw_game_texture(texture_id, width, height):
    """Draw the game texture to fill the screen."""
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    gl.glColor4f(1, 1, 1, 1)
    gl.glBegin(gl.GL_QUADS)
    gl.glTexCoord2f(0, 0); gl.glVertex2f(0, 0)
    gl.glTexCoord2f(1, 0); gl.glVertex2f(width, 0)
    gl.glTexCoord2f(1, 1); gl.glVertex2f(width, height)
    gl.glTexCoord2f(0, 1); gl.glVertex2f(0, height)
    gl.glEnd()
    gl.glDisable(gl.GL_TEXTURE_2D)

# Initialize font for FPS counter
fps_font = pygame.font.SysFont('Arial', 30)

# Load sprite sheets
load_sprite_sheets()
load_visual_sheets()

combat_handler = CombatHandler()
state_machine = StateMachine()
sound_handler = SoundHandler()


parser = argparse.ArgumentParser()
parser.add_argument("--no_dev", action="store_true", default=False)
args = parser.parse_args()

scene_manager.initialize(game_surface, developer_mode=not args.no_dev)
selected_unit_manager.initialize(scene_manager.manager)

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    dt = clock.tick(timing.get_max_fps()) / 1000
    
    # Check if pygame is still initialized before getting events
    if not pygame.get_init():
        break
        
    events = pygame.event.get()

    # Process modifier key events for info mode before scene processing
    for event in events:
        if event.type == pygame.KEYDOWN:
            # Check for the appropriate modifier key based on platform
            modifier_pressed = False
            if sys.platform == 'darwin':
                # macOS: Use Command key
                modifier_pressed = event.key == pygame.K_LMETA or event.key == pygame.K_RMETA
            else:
                # Windows/Linux: Use Alt key
                modifier_pressed = event.key == pygame.K_LALT or event.key == pygame.K_RALT
                
            if modifier_pressed:
                old_info_mode = info_mode_manager.info_mode
                info_mode_manager.info_mode = not info_mode_manager.info_mode
                
                # Handle mode transitions
                if old_info_mode and not info_mode_manager.info_mode:
                    # Exiting info mode - clear all cards
                    selected_unit_manager.clear_all_cards()
                elif not old_info_mode and info_mode_manager.info_mode:
                    # Entering info mode - if there's a current card, move it to info mode collection
                    if selected_unit_manager.unit_card is not None:
                        selected_unit_manager.unit_cards.append(selected_unit_manager.unit_card)
                        selected_unit_manager.unit_card = None
                
        # Process selected unit manager events (for future interactive features)
        selected_unit_manager.process_events(event)

    # Clear OpenGL screen
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    
    # Clear game surface with transparency so OpenGL shows through
    game_surface.fill((0, 0, 0, 0))
    
    # Reset dirty flag before scene update
    surface_dirty = False
    
    # Update scene (renders to game_surface)
    running = scene_manager.update(dt, events)
    
    # Only convert to OpenGL and flip if content was drawn
    if surface_dirty:
        game_texture = surface_to_texture(game_surface)
        draw_game_texture(game_texture, screen_width, screen_height)
        gl.glDeleteTextures([game_texture])
        pygame.display.flip()
        timing.tick()
    else:
        # No content drawn - skip expensive operations
        # Previous frame remains visible
        pass

pygame.quit()
