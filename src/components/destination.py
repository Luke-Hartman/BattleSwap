"""
This module contains the Destination component, which represents a destination strategy.
"""

import esper
from dataclasses import dataclass
from components.orientation import FacingDirection, Orientation
from components.team import Team, TeamType
from target_strategy import TargetStrategy
from components.position import Position
from components.velocity import Velocity

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

    def get_destination_position(self, entity: int, dt: float) -> Position:
        """Calculate the destination position based on the current target.
        
        Args:
            entity: The entity ID that owns this destination
            dt: Delta time for velocity prediction
            
        Returns:
            Tuple of (x, y) destination coordinates
        """
        target = self.target_strategy.target
        assert target is not None, "Target strategy must have a target"
            
        target_pos = esper.component_for_entity(target, Position)
        target_velocity = esper.component_for_entity(target, Velocity)
        
        team = esper.component_for_entity(entity, Team)
        orientation = esper.component_for_entity(entity, Orientation)
        
        destination_x = target_pos.x + self.get_x_offset(team.type, orientation.facing)
        destination_y = target_pos.y
        
        # Predict target movement
        destination_x += target_velocity.x * dt
        destination_y += target_velocity.y * dt
        
        return Position(destination_x, destination_y)
