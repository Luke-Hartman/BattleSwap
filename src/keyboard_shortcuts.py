"""Centralized keyboard shortcut formatting for UI buttons.

This module provides utilities for consistently formatting button text
with keyboard shortcuts across the entire game.
"""

import sys

SHORTCUT_FORMAT = "{text} ({key})"

class KeyboardShortcuts:
    """Constants for keyboard shortcuts used throughout the game."""
    
    # Navigation shortcuts
    ESCAPE = "Esc"
    ENTER = "Enter"
    TAB = "Tab"
    
    # Time control shortcuts
    SPACE = "Space"
    PLUS = "+"
    MINUS = "-"
    
    # UI shortcuts
    U = "U"


def format_button_text(text: str, key: str) -> str:
    """Format button text with a keyboard shortcut.
    
    Args:
        text: The base button text
        key: The keyboard shortcut key name
        
    Returns:
        Formatted text with keyboard shortcut
        
    Examples:
        >>> format_button_text("Return", KeyboardShortcuts.ESCAPE)
        "[Esc] Return"
        >>> format_button_text("Start Battle", KeyboardShortcuts.ENTER)
        "[Enter] Start Battle"
    """
    return SHORTCUT_FORMAT.format(key=key, text=text)
