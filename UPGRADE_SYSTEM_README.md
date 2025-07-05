# BattleSwap Unit Upgrade System

## Overview

The BattleSwap Unit Upgrade System allows players to enhance their units with specific upgrades that provide detailed descriptions and percentage-based improvements. Each upgrade shows exactly what it does, including specific percentages like "increases damage by 33.33%".

## Files Added

### Core System Files

1. **`data/upgrade_data.json`** - Contains all upgrade definitions with descriptions and effects
2. **`src/upgrade_manager.py`** - Manages player upgrades and upgrade points
3. **`src/ui_components/upgrade_window.py`** - UI component for displaying and purchasing upgrades
4. **`demo_upgrade_system.py`** - Demonstration script showing the upgrade system in action

## Key Features

### Human-Readable Descriptions
- Every upgrade has a clear description with specific percentages
- Examples: "Increases damage by 33.33%", "Reduces reload time by 25.00%"
- Descriptions include total effects for stacking upgrades
- Prerequisites are clearly displayed

### Comprehensive Upgrade Coverage
- **Core Units**: Archer, Barbarian, Cavalry, Duelist, Longbowman, Swordsman, Wizard
- **Crusader Units**: Banner Bearer, Black Knight, Catapult, Cleric, Commander, Crossbowman, Defender, Gold Knight, Guardian Angel, Paladin, Pikeman, Red Knight, Soldier
- **Other Units**: Werebear, Zombie variants (Basic, Brute, Grabber, Jumper, Spitter, Tank)

### Upgrade Types
- **Damage Multipliers**: Direct damage increases
- **Health Multipliers**: Increased survivability  
- **Speed Multipliers**: Movement and attack speed improvements
- **Range Multipliers**: Extended attack/ability ranges
- **Special Effects**: Unique abilities like piercing, area effects, critical hits
- **Aura Effects**: Buffs that affect nearby allies
- **Defensive Abilities**: Damage reduction, armor, regeneration

### Prerequisite System
- Some upgrades require others to be purchased first
- Clear prerequisite display in the UI
- Logical upgrade trees (e.g., basic damage → advanced damage → master effects)

## Usage

### Opening the Upgrade Window

```python
from ui_components.upgrade_window import UpgradeWindow
from components.unit_type import UnitType

# Create upgrade window for a specific unit
upgrade_window = UpgradeWindow(manager, UnitType.CORE_ARCHER)
```

### Managing Upgrades

```python
from upgrade_manager import upgrade_manager

# Get current upgrade points
points = upgrade_manager.get_upgrade_points()

# Get owned upgrades for a unit
owned = upgrade_manager.get_owned_upgrades(UnitType.CORE_ARCHER)

# Purchase an upgrade
success = upgrade_manager.purchase_upgrade(UnitType.CORE_ARCHER, "archer_damage_1")

# Get combined effects of all upgrades
effects = upgrade_manager.get_upgrade_effects(UnitType.CORE_ARCHER)
```

### Running the Demo

```bash
python demo_upgrade_system.py
```

## Example Upgrades

### Core Archer Upgrades
- **Improved Arrows**: Increases damage by 25.00%
- **Extended Bow**: Increases range by 20.00%  
- **Swift Archer**: Increases movement speed by 15.00%
- **Masterwork Arrows**: Increases damage by 50.00% (total 87.50% increase) - requires Improved Arrows

### Crusader Black Knight Upgrades  
- **Terrifying Presence**: Fear effect radius increased by 75.00%
- **Cursed Blade**: Increases damage by 35.00%
- **Shadow Step**: Increases movement speed by 40.00%
- **Death's Embrace**: Instantly kills enemies below 25.00% health - requires Cursed Blade + Terrifying Presence

### Zombie Brute Upgrades
- **Crushing Blows**: Increases damage by 50.00%
- **Massive Frame**: Increases health by 75.00%
- **Zombie Carrier**: Carries 2 additional zombies into battle
- **Ground Smash**: Attacks create shockwaves dealing 75.00% damage in a large area

## Integration Points

### With Existing Systems

The upgrade system is designed to integrate with:

1. **Unit Creation**: Apply upgrade effects when units are created
2. **Battle System**: Modify unit stats based on owned upgrades  
3. **Progress System**: Award upgrade points for completing battles
4. **Save System**: Persist upgrade ownership and points

### Recommended Integration

```python
# In unit creation
def create_unit(unit_type, position, team):
    unit = base_create_unit(unit_type, position, team)
    
    # Apply upgrades
    effects = upgrade_manager.get_upgrade_effects(unit_type)
    apply_upgrade_effects(unit, effects)
    
    return unit

# In battle completion
def on_battle_complete(difficulty, performance):
    points = calculate_upgrade_points(difficulty, performance)
    upgrade_manager.add_upgrade_points(points)

# In UI (right-click unit card, upgrade button, etc.)
def show_unit_upgrades(unit_type):
    upgrade_window = UpgradeWindow(ui_manager, unit_type)
```

## Upgrade Data Structure

Each upgrade in `upgrade_data.json` follows this structure:

```json
{
    "id": "unique_upgrade_id",
    "name": "Display Name",
    "description": "Human readable description with percentages",
    "effect": {
        "damage_multiplier": 1.25,
        "range_multiplier": 1.20
    },
    "cost": 50,
    "prerequisites": ["other_upgrade_id"]
}
```

## Future Enhancements

- Visual upgrade trees/skill trees
- Upgrade categories and filtering
- Upgrade presets/builds
- Upgrade point economy balancing
- Integration with existing corruption system
- Upgrade effects visualization in battle

## Testing

Run the demo script to test all features:
- Purchase upgrades and see immediate UI updates
- Test prerequisite system
- Verify upgrade point deduction
- Switch between different unit types
- See combined upgrade effects

The upgrade system is fully functional and ready for integration into the main game!