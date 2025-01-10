"""
This module contains the Destination component, which represents a destination strategy.
"""

from dataclasses import dataclass
from components.orientation import FacingDirection
from components.team import Team, TeamType
from target_strategy import TargetStrategy

@dataclass
class Destination:
    """Represents a destination strategy."""

    target_strategy: TargetStrategy
    """The target strategy."""

    x_offset: float
    """The x-offset from the target's position that the unit tries to reach.
    
    This is to prevent units from walking directly towards their target.
    Instead, they will try to walk towards their target's position offset
    by this amount towards the side they are already on.
    """

    use_team_x_offset: bool = False
    """Whether to use the team's x-offset, rather than basing on which side of the target the unit is on.
    
    (Team 1 is on the left, Team 2 is on the right).
    """

    min_distance: float = 1
    """The unit will stop moving when it is within this distance of the target."""

    def get_x_offset(self, team: TeamType, facing: FacingDirection) -> float:
        if self.use_team_x_offset:
            return self.x_offset * (-1 if team == TeamType.TEAM1 else 1)
        return -self.x_offset * facing.value
