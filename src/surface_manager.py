"""Surface management utilities for tracking surface state.

This module provides functionality to track whether the game surface has been
modified and needs to be redrawn.
"""

# Flag to track when content has been drawn to the surface
_surface_dirty = False


def mark_surface_dirty() -> None:
    """Mark the game surface as dirty (content has been drawn to it)."""
    global _surface_dirty
    _surface_dirty = True


def is_surface_dirty() -> bool:
    """Get the current dirty state of the game surface.
    
    Returns:
        True if the surface has been modified and needs redrawing, False otherwise.
    """
    return _surface_dirty


def reset_surface_dirty() -> None:
    """Reset the surface dirty flag to False."""
    global _surface_dirty
    _surface_dirty = False