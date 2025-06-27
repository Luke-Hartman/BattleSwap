# Unit Tier System Implementation

## Overview

The unit tier system has been successfully implemented in BattleSwap, providing three main capabilities:

1. **Unit cards show correct tier when hovering** - Mouse hover over units or barracks icons displays unit cards matching the unit's current tier
2. **Player units use current tier** - All player units in-game reflect their upgraded tier, with world map rebuilds when units are upgraded and correct tier usage during unit placement  
3. **Enemy units remain basic tier** - Enemy units always use basic tier regardless of player upgrades

## Core Components

### UnitTier Enum (`src/components/unit_tier.py`)
- **BASIC**: Default tier for all units
- **ADVANCED**: First upgrade tier
- **ELITE**: Maximum upgrade tier

### Progress Manager Integration (`src/progress_manager.py`)
- `unit_tiers: Dict[UnitType, UnitTier]` - Tracks current tier for each unit type
- `get_unit_tier(unit_type)` - Returns current tier or BASIC if not upgraded
- `can_upgrade_unit(unit_type)` - Checks if upgrade is possible (requires credits)
- `upgrade_unit(unit_type)` - Upgrades unit and triggers world map rebuild
- `advanced_credits` and `elite_credits` - Currency for upgrades

## Implementation Details

### 1. Unit Card Display (`src/selected_unit_manager.py`)
```python
# Uses current tier from progress manager
unit_tier = progress_manager.get_unit_tier(unit_type) if progress_manager else UnitTier.BASIC
```
- Unit cards automatically display stats and information for the unit's current tier
- Hovering over units or barracks icons shows the correct tier information

### 2. Player vs Enemy Unit Creation

#### World Map View (`src/world_map_view.py`)
```python
# Player units use their current tier
tier = progress_manager.get_unit_tier(unit_type) if progress_manager else UnitTier.BASIC

# Enemy units are always basic tier  
tier = UnitTier.BASIC
```

#### Setup Battle Scene (`src/scenes/setup_battle.py`)
```python
# Uses appropriate tier based on team
if placement_team == TeamType.TEAM1:
    # Player units use their current tier
    tier = progress_manager.get_unit_tier(value) if progress_manager else UnitTier.BASIC
else:
    # Enemy units are always basic tier
    tier = UnitTier.BASIC
```

### 3. Unit Creation Infrastructure (`src/entities/units.py`)
- All `create_unit` functions accept a `tier` parameter with BASIC default
- `unit_base_entity()` properly applies tier-based modifications
- Unit stats are modified based on tier (e.g., archer damage multipliers)
- `get_unit_sprite_sheet()` supports tier-specific visuals

### 4. Battle Simulation (`src/auto_battle.py`)
- Battle simulations use BASIC tier for both teams for consistency
- Ensures fair simulation regardless of player upgrades

### 5. Effects and Special Cases
- **Effect-created units** (`src/effects.py`): Use BASIC tier
- **Zombie infections** (`src/processors/dying_processor.py`): Always create BASIC tier zombies
- **World map rebuilds**: Automatically triggered when units are upgraded

## Tier-Based Modifications

The system supports tier-based stat modifications, implemented in individual unit creation functions. For example:

```python
# Core Archer damage scaling by tier
arrow_damage = gc.CORE_ARCHER_ATTACK_DAMAGE
if tier == UnitTier.ADVANCED:
    arrow_damage = arrow_damage * 1.5
elif tier == UnitTier.ELITE:
    arrow_damage = arrow_damage * 2
```

## World Map Synchronization

When units are upgraded:
1. `upgrade_unit()` method updates the tier in progress manager
2. World map automatically rebuilds when scenes transition
3. All existing player units reflect the new tier
4. Enemy units remain unaffected at BASIC tier

## Safety Features

- **Null safety**: All tier queries check if progress_manager exists
- **Default behavior**: Falls back to BASIC tier if progress manager is unavailable
- **Type consistency**: Proper imports and type checking throughout the system
- **Battle simulation integrity**: Uses BASIC tier for fair simulation results

## Usage Examples

### Checking Unit Tier
```python
current_tier = progress_manager.get_unit_tier(UnitType.CORE_ARCHER)
```

### Creating Player Unit
```python
tier = progress_manager.get_unit_tier(unit_type) if progress_manager else UnitTier.BASIC
create_unit(x, y, unit_type, TeamType.TEAM1, corruption_powers, tier)
```

### Creating Enemy Unit
```python
create_unit(x, y, unit_type, TeamType.TEAM2, corruption_powers, UnitTier.BASIC)
```

## Integration Points

The tier system integrates seamlessly with:
- **UI Components**: Barracks, unit cards, progress panels
- **Battle System**: Unit creation, world map, setup scenes
- **Progress System**: Save/load, upgrade mechanics
- **Corruption System**: Tier-aware corruption application
- **Visual System**: Tier-specific sprite sheets and animations

## File Changes Made

1. **`src/auto_battle.py`**: Added tier parameter to create_unit calls
2. **`src/effects.py`**: Added tier parameter to CreatesUnit effect
3. **`src/processors/dying_processor.py`**: Added tier parameter for zombie creation
4. **`src/selected_unit_manager.py`**: Already implemented tier-aware unit cards
5. **`src/world_map_view.py`**: Already implemented tier-based unit creation
6. **`src/scenes/setup_battle.py`**: Already implemented tier logic for unit placement

## Status: ✅ COMPLETE

All three main requirements have been successfully implemented:
- ✅ Unit cards show correct tier when hovering
- ✅ Player units use current tier throughout the game
- ✅ Enemy units remain basic tier regardless of player upgrades

The system is fully functional and integrated with all existing game systems.