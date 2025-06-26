from components.unit_type import UnitType, UnitTier
from typing import Dict
from game_constants import gc

def get_unit_value(unit_type: UnitType) -> int:
    """Get the point value for a unit, adjusting for tier."""
    base_unit = unit_type.get_base_unit_type()
    base_value = _base_unit_values.get(base_unit, 0)
    
    tier = unit_type.get_tier()
    if tier == UnitTier.BASIC:
        return base_value
    elif tier == UnitTier.VETERAN:
        return int(base_value * 1.5)  # 50% more points for veteran
    elif tier == UnitTier.ELITE:
        return int(base_value * 2.0)  # 100% more points for elite
    else:
        return base_value

_base_unit_values: Dict[UnitType, int] = {
    UnitType.CORE_ARCHER: gc.CORE_ARCHER_POINTS,
    UnitType.CORE_BARBARIAN: gc.CORE_BARBARIAN_POINTS,
    UnitType.CORE_CAVALRY: gc.CORE_CAVALRY_POINTS,
    UnitType.CORE_DUELIST: gc.CORE_DUELIST_POINTS,
    UnitType.CORE_LONGBOWMAN: gc.CORE_LONGBOWMAN_POINTS,
    UnitType.CORE_SWORDSMAN: gc.CORE_SWORDSMAN_POINTS,
    UnitType.CORE_WIZARD: gc.CORE_WIZARD_POINTS,
    UnitType.CRUSADER_BANNER_BEARER: gc.CRUSADER_BANNER_BEARER_POINTS,
    UnitType.CRUSADER_BLACK_KNIGHT: gc.CRUSADER_BLACK_KNIGHT_POINTS,
    UnitType.CRUSADER_CATAPULT: gc.CRUSADER_CATAPULT_POINTS,
    UnitType.CRUSADER_CLERIC: gc.CRUSADER_CLERIC_POINTS,
    UnitType.CRUSADER_COMMANDER: gc.CRUSADER_COMMANDER_POINTS,
    UnitType.CRUSADER_CROSSBOWMAN: gc.CRUSADER_CROSSBOWMAN_POINTS,
    UnitType.CRUSADER_DEFENDER: gc.CRUSADER_DEFENDER_POINTS,
    UnitType.CRUSADER_GOLD_KNIGHT: gc.CRUSADER_GOLD_KNIGHT_POINTS,
    UnitType.CRUSADER_GUARDIAN_ANGEL: gc.CRUSADER_GUARDIAN_ANGEL_POINTS,
    UnitType.CRUSADER_PALADIN: gc.CRUSADER_PALADIN_POINTS,
    UnitType.CRUSADER_PIKEMAN: gc.CRUSADER_PIKEMAN_POINTS,
    UnitType.CRUSADER_RED_KNIGHT: gc.CRUSADER_RED_KNIGHT_POINTS,
    UnitType.CRUSADER_SOLDIER: gc.CRUSADER_SOLDIER_POINTS,
    UnitType.WEREBEAR: gc.WEREBEAR_POINTS,
    UnitType.ZOMBIE_BASIC_ZOMBIE: gc.ZOMBIE_BASIC_ZOMBIE_POINTS,
    UnitType.ZOMBIE_BRUTE: gc.ZOMBIE_BRUTE_POINTS,
    UnitType.ZOMBIE_GRABBER: gc.ZOMBIE_GRABBER_POINTS,
    UnitType.ZOMBIE_JUMPER: gc.ZOMBIE_JUMPER_POINTS,
    UnitType.ZOMBIE_SPITTER: gc.ZOMBIE_SPITTER_POINTS,
    UnitType.ZOMBIE_TANK: gc.ZOMBIE_TANK_POINTS,
}

# Backward compatibility
unit_values = _base_unit_values