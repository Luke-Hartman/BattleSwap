"""Stance component.

Stances are used for units who can toggle between different states.

The meaning of each stance is defined by the unit type, and should use constants within that unit type.
"""


class Stance:
    """A stance component."""

    def __init__(self, stance: int):
        self.stance = stance
