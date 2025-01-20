"""Component for tracking unit types in the game."""

from enum import Enum

class UnitType(str, Enum):
    """Enum representing different types of units."""
    CORE_ARCHER = "CORE_ARCHER"
    CORE_CAVALRY = "CORE_CAVALRY"
    CORE_DUELIST = "CORE_DUELIST"
    CORE_WIZARD = "CORE_WIZARD"
    CORE_SWORDSMAN = "CORE_SWORDSMAN"
    CRUSADER_BANNER_BEARER = "CRUSADER_BANNER_BEARER"
    CRUSADER_BLACK_KNIGHT = "CRUSADER_BLACK_KNIGHT"
    CRUSADER_CATAPULT = "CRUSADER_CATAPULT"
    CRUSADER_CLERIC = "CRUSADER_CLERIC"
    CRUSADER_COMMANDER = "CRUSADER_COMMANDER"
    CRUSADER_CROSSBOWMAN = "CRUSADER_CROSSBOWMAN"
    CRUSADER_DEFENDER = "CRUSADER_DEFENDER"
    CRUSADER_GOLD_KNIGHT = "CRUSADER_GOLD_KNIGHT"
    CRUSADER_GUARDIAN_ANGEL = "CRUSADER_GUARDIAN_ANGEL"
    CRUSADER_LONGBOWMAN = "CRUSADER_LONGBOWMAN"
    CRUSADER_PALADIN = "CRUSADER_PALADIN"
    CRUSADER_PIKEMAN = "CRUSADER_PIKEMAN"
    CRUSADER_RED_KNIGHT = "CRUSADER_RED_KNIGHT"
    CRUSADER_SOLDIER = "CRUSADER_SOLDIER"
    ZOMBIE_BASIC_ZOMBIE = "ZOMBIE_BASIC_ZOMBIE"
    WEREBEAR = "WEREBEAR"

class UnitTypeComponent:
    """Component that stores the type of a unit."""
    
    def __init__(self, type: UnitType):
        """Initialize the UnitType component.
        
        Args:
            type: The type of unit this component represents
        """
        self.type = type

