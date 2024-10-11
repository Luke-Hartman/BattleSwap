"""Team component for the Battle Swap game."""

from dataclasses import dataclass
from enum import Enum, auto

class TeamType(Enum):
    """Enum representing different team types."""
    ALLY = auto()
    ENEMY = auto()

@dataclass
class Team:
    """Represents the team affiliation of an entity."""

    team_type: TeamType
    """The type of team the entity belongs to."""