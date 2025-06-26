#!/usr/bin/env python3
"""Simple test to verify the tier system works."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from components.unit_type import UnitType, UnitTier
from entities.units import get_health_for_tier, get_tier_suffix
from unit_values import get_unit_value

def test_tier_system():
    """Test the basic tier system functionality."""
    print("Testing Unit Tier System")
    print("=" * 40)
    
    # Test basic unit
    basic_archer = UnitType.CORE_ARCHER
    print(f"Basic Archer: {basic_archer}")
    print(f"  Tier: {basic_archer.get_tier()}")
    print(f"  Base Unit: {basic_archer.get_base_unit_type()}")
    print(f"  Suffix: '{get_tier_suffix(basic_archer.get_tier())}'")
    print(f"  Health (base 280): {get_health_for_tier(280, basic_archer.get_tier())}")
    print(f"  Point Value: {get_unit_value(basic_archer)}")
    print()
    
    # Test veteran unit
    veteran_archer = UnitType.CORE_ARCHER_VETERAN
    print(f"Veteran Archer: {veteran_archer}")
    print(f"  Tier: {veteran_archer.get_tier()}")
    print(f"  Base Unit: {veteran_archer.get_base_unit_type()}")
    print(f"  Suffix: '{get_tier_suffix(veteran_archer.get_tier())}'")
    print(f"  Health (base 280): {get_health_for_tier(280, veteran_archer.get_tier())}")
    print(f"  Point Value: {get_unit_value(veteran_archer)}")
    print()
    
    # Test elite unit
    elite_archer = UnitType.CORE_ARCHER_ELITE
    print(f"Elite Archer: {elite_archer}")
    print(f"  Tier: {elite_archer.get_tier()}")
    print(f"  Base Unit: {elite_archer.get_base_unit_type()}")
    print(f"  Suffix: '{get_tier_suffix(elite_archer.get_tier())}'")
    print(f"  Health (base 280): {get_health_for_tier(280, elite_archer.get_tier())}")
    print(f"  Point Value: {get_unit_value(elite_archer)}")
    print()
    
    # Test tier conversion
    print("Tier Conversion Tests:")
    print(f"  Basic -> Veteran: {basic_archer.get_tiered_version(UnitTier.VETERAN)}")
    print(f"  Basic -> Elite: {basic_archer.get_tiered_version(UnitTier.ELITE)}")
    print(f"  Veteran -> Basic: {veteran_archer.get_tiered_version(UnitTier.BASIC)}")
    print(f"  Elite -> Basic: {elite_archer.get_tiered_version(UnitTier.BASIC)}")
    print()
    
    print("All tests completed successfully!")

if __name__ == "__main__":
    test_tier_system()