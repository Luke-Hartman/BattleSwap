"""Team component module for Battle Swap.

This module contains the Team component, which represents which team an entity belongs to.
"""

from dataclasses import dataclass
from enum import Enum, auto

class TeamType(int, Enum):
    """Enum representing different teams in the game."""

    TEAM1 = 1
    """Team 1, facing right."""

    TEAM2 = 2
    """Team 2, facing left."""

    def other(self) -> "TeamType":
        """Get the other team."""
        return TeamType.TEAM2 if self == TeamType.TEAM1 else TeamType.TEAM1

@dataclass
class Team:
    """Represents the team of an entity."""

    type: TeamType
    """The team the entity belongs to."""
