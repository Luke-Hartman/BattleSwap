"""Stance component.

Stances are used for units who can toggle between different states.

The meaning of each stance is defined by the unit type, and should use constants within that unit type.
"""

from dataclasses import dataclass

@dataclass
class Stance:
    """A stance component."""

    stance: int
    """The stance."""
