"""Component for tracking unit types in the game."""

from enum import Enum, auto

class UnitType(Enum):
    """Enum representing different types of units."""
    SWORDSMAN = auto()
    ARCHER = auto()
    MAGE = auto()
    HORSEMAN = auto()
    WEREBEAR = auto()
    FANCY_SWORDSMAN = auto()
    LONGBOWMAN = auto()
class UnitTypeComponent:
    """Component that stores the type of a unit."""
    
    def __init__(self, type: UnitType):
        """Initialize the UnitType component.
        
        Args:
            type: The type of unit this component represents
        """
        self.type = type

