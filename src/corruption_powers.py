"""Module for corruption powers that can be applied to battles."""

from typing import Annotated, Optional, Union, Literal
from abc import abstractmethod
from pydantic import BaseModel, Field, ConfigDict
from components.team import TeamType

class CorruptionPower(BaseModel):
    """Base class for corruption powers."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(..., description="The name of the power")

    required_team: Optional[TeamType]

    @property
    @abstractmethod
    def description(self) -> str:
        """A human-readable description of what the power does."""
        raise NotImplementedError("Subclasses must implement description")

def _get_team_str(team: Optional[TeamType]) -> str:
    if team is None:
        return "All"
    if team == TeamType.TEAM1:
        return "Allied"
    if team == TeamType.TEAM2:
        return "Enemy"

def _get_increase_str(increase_percent: float) -> str:
    if increase_percent > 0:
        return f"{int(increase_percent)}% increased"
    else:
        return f"{-int(increase_percent)}% decreased"

class IncreasedMaxHealth(CorruptionPower):
    """Power that increases the maximum health of enemy units."""
    name: Literal["increased_max_health"] = Field("increased_max_health", description="The name of the power")
    increase_percent: float = Field(
        ..., 
        description="Percentage to increase health by",
    )

    @property
    def description(self) -> str:
        """Generate a description based on the increase percentage."""
        return f"{_get_team_str(self.required_team)} units have {_get_increase_str(self.increase_percent)} maximum health"

class IncreasedDamage(CorruptionPower):
    """Power that increases the damage of enemy units."""
    name: Literal["increased_damage"] = Field("increased_damage", description="The name of the power")
    increase_percent: float = Field(
        ..., 
        description="Percentage to increase damage by",
    )

    @property
    def description(self) -> str:
        """Generate a description based on the increase percentage."""
        return f"{_get_team_str(self.required_team)} units have {_get_increase_str(self.increase_percent)} damage"


class IncreasedMovementSpeed(CorruptionPower):
    """Power that increases the movement speed of enemy units."""
    name: Literal["increased_movement_speed"] = Field("increased_movement_speed", description="The name of the power")
    increase_percent: float = Field(
        ..., 
        description="Percentage to increase movement speed by",
    )

    @property
    def description(self) -> str:
        """Generate a description based on the increase percentage."""
        return f"{_get_team_str(self.required_team)} units have {_get_increase_str(self.increase_percent)} movement speed"


class IncreasedAbilitySpeed(CorruptionPower):
    """Power that increases the ability speed of enemy units."""
    name: Literal["increased_ability_speed"] = Field("increased_ability_speed", description="The name of the power")
    increase_percent: float = Field(
        ..., 
        description="Percentage to increase ability speed by",
    )

    @property
    def description(self) -> str:
        """Generate a description based on the increase percentage."""
        return f"{_get_team_str(self.required_team)} units have {_get_increase_str(self.increase_percent)} ability speed"


CorruptionPowerUnion = Annotated[
    Union[IncreasedMaxHealth, IncreasedDamage, IncreasedMovementSpeed, IncreasedAbilitySpeed],
    Field(discriminator='name')
] 