"""
Screen dimensions utility module.

This module provides access to the actual screen dimensions determined at runtime,
avoiding the macOS dock/menubar issues with pygame.display.Info().
"""

# These will be set by main.py after window creation
screen_width: int = 0
screen_height: int = 0

def set_dimensions(width: int, height: int) -> None:
    """Set the actual screen dimensions after window creation."""
    global screen_width, screen_height
    screen_width = width
    screen_height = height

def get_dimensions() -> tuple[int, int]:
    """Get the actual screen dimensions."""
    return screen_width, screen_height

def get_width() -> int:
    """Get the actual screen width."""
    return screen_width

def get_height() -> int:
    """Get the actual screen height."""
    return screen_height