"""Component for tracking unit types in the game."""

from enum import Enum, auto

class UnitType(Enum):
    """Enum representing different types of units."""
    CORE_SWORDSMAN = auto()
    CORE_ARCHER = auto()
    CORE_MAGE = auto()
    CORE_HORSEMAN = auto()
    WEREBEAR = auto()
    CORE_DUELIST = auto()
    CRUSADER_BLACK_KNIGHT = auto()
    CRUSADER_CLERIC = auto()
    CRUSADER_COMMANDER = auto()
    CRUSADER_DEFENDER = auto()
    CRUSADER_GOLD_KNIGHT = auto()
    CRUSADER_LONGBOWMAN = auto()
    CRUSADER_PALADIN = auto()
    CRUSADER_PIKEMAN = auto()
    CRUSADER_RED_KNIGHT = auto()

class UnitTypeComponent:
    """Component that stores the type of a unit."""
    
    def __init__(self, type: UnitType):
        """Initialize the UnitType component.
        
        Args:
            type: The type of unit this component represents
        """
        self.type = type

