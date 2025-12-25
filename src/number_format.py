"""Utility functions for formatting numbers for display.

This module provides functions to format numbers consistently across the game,
ensuring that integer values are displayed as integers rather than floats.
"""

from typing import Union


def format_number(value: Union[int, float]) -> str:
    """Format a number for display, showing integers as integers.
    
    If the value is effectively an integer (within floating point precision),
    it will be displayed as an integer. Otherwise, it will be displayed
    as a float with 1 decimal place.
    
    Args:
        value: The number to format (int or float)
        
    Returns:
        String representation of the number
        
    Examples:
        >>> format_number(2.0)
        '2'
        >>> format_number(2.5)
        '2.5'
        >>> format_number(2.1)
        '2.1'
        >>> format_number(2)
        '2'
    """
    # Handle integers directly
    if isinstance(value, int):
        return str(value)
    
    # Check if float is effectively an integer
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    
    # Format as float with 1 decimal place
    return f"{value:.1f}"

