import enum
from components.unit_tier import UnitTier
from components.unit_type import UnitType
from game_constants import gc
from typing import Dict, List, Optional
from dataclasses import dataclass

def taper(value: float) -> float:
    """Tapers the value to a stat value between 1 and 20, with a steeper curve at the end."""
    if value < 14:
        return value
    return 14 + min((value - 14)**0.5, 6)

def damage_stat(dps: float, multiplier: float = 1) -> float:
    """Maps damage to a stat value between 1 and 10."""
    stat = (dps * multiplier) / (gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE / gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION) * 5
    return taper(stat)

def healing_stat(healing_dps: float) -> float:
    """Maps healing to a stat value between 1 and 10."""
    return damage_stat(healing_dps, 2)

def defense_stat(defense: float, armored: bool = False, heavily_armored: bool = False, self_heal_dps: float = 0) -> float:
    """Maps defense to a stat value between 1 and 10."""
    stat = defense / gc.ZOMBIE_TANK_HP * 16 + self_heal_dps * 2 / (gc.CORE_SWORDSMAN_ATTACK_DAMAGE / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION) * 5
    if armored:
        stat *= 1.25
    if heavily_armored:
        stat *= 1.5
    assert not (armored and heavily_armored), "Cannot be both armored and heavily armored"
    return taper(stat)

def speed_stat(movement_speed: float) -> float:
    """Maps movement speed to a stat value between 1 and 10."""
    nine_speed = gc.CORE_CAVALRY_MOVEMENT_SPEED
    stat = (movement_speed / nine_speed) * 18
    return taper(stat)

def range_stat(range: float) -> float:
    """Maps range to a stat value between 1 and 10."""
    stat = (range / gc.CRUSADER_CATAPULT_MAXIMUM_RANGE) * 24
    return taper(stat)

class GlossaryEntryType(enum.Enum):
    """Types of glossary entries available in the game."""
    AREA_OF_EFFECT = "Area of Effect" 
    ARMORED = "Armored"
    AURA = "Aura"
    BARRACKS = "Barracks"
    CORRUPTION = "Corruption"
    FACTION = "Faction"
    FLEE = "Flee"   
    FOLLOWER = "Follower"
    HEAVILY_ARMORED = "Heavily Armored"
    HUNTER = "Hunter"
    POISON = "Poison"
    INFECTION = "Infection"
    KILLING_BLOW = "Killing Blow"
    POINTS = "Points"
    SPREADER = "Spreader"
    UPGRADE = "Upgrade"

class StatType(enum.Enum):
    """Types of stats that units can have."""
    DAMAGE = "damage"
    DEFENSE = "defense"
    SPEED = "speed"
    RANGE = "range"
    UTILITY = "utility"

@dataclass
class UnitData:
    """Data class representing unit information including stats, tooltips, and tips."""
    name: str
    description: str
    tier: UnitTier
    stats: Dict[StatType, Optional[float]]
    tooltips: Dict[StatType, Optional[str]]
    tips: Dict[str, List[str]]
    modification_levels: Dict[StatType, int]
    
    def __post_init__(self):
        """Ensure all StatType values are explicitly specified."""
        # Fill in missing stats with None
        for stat_type in StatType:
            if stat_type not in self.stats:
                raise ValueError(f"Stat type {stat_type} not found in stats")
            if stat_type not in self.tooltips:
                raise ValueError(f"Stat type {stat_type} not found in tooltips")

# Glossary entry content
GLOSSARY_ENTRIES = {
    GlossaryEntryType.AREA_OF_EFFECT: "Area of Effect: Applies one or more effects to all units within an area. Some units may not be affected, such as units on the same team.",
    GlossaryEntryType.ARMORED: f"Armored units take {gc.ARMOR_FLAT_DAMAGE_REDUCTION} flat reduced damage, and have {gc.ARMOR_PERCENT_DAMAGE_REDUCTION}% damage reduction (after flat reduction). Maximum damage reduction is capped at {gc.MAX_ARMOR_DAMAGE_REDUCTION}%. Also see <a href='{GlossaryEntryType.HEAVILY_ARMORED.value}'>Heavily Armored</a>.",
    GlossaryEntryType.AURA: "Auras apply effects to nearby units. Some units may not be affected, such as units on the same team.",
    GlossaryEntryType.BARRACKS: "The Barracks contains your available army. It can be accessed at the bottom of the screen.",
    GlossaryEntryType.CORRUPTION: f"Corruption reopens up to {gc.CORRUPTION_BATTLE_COUNT} battle or upgrade hexes you've already claimed, with modifiers to increase their difficulty including <a href='{GlossaryEntryType.UPGRADE.value}'>upgrading</a> all enemy units to Elite. To continue, you must reclaim these hexes. Corruption can activate when you exceed {gc.CORRUPTION_TRIGGER_POINTS} <a href='{GlossaryEntryType.POINTS.value}'>Points</a> in your <a href='{GlossaryEntryType.BARRACKS.value}'>Barracks</a>. Corruption is required to <a href='{GlossaryEntryType.UPGRADE.value}'>upgrade</a> your units to Elite. Efficient players can corrupt and reclaim every battle.",
    GlossaryEntryType.FACTION: "Factions are groups of units that share a common theme. Enemy armies are made up of units from a specific faction plus the core units, while players are free to mix and match units from different factions.",
    GlossaryEntryType.FLEE: "Fleeing units move away from the source of the effect at a reduced speed for 2 seconds.",
    GlossaryEntryType.FOLLOWER: "Follower units follow a nearby friendly non-follower unit until it is killed.",
    GlossaryEntryType.HEAVILY_ARMORED: f"Heavily Armored units take {gc.HEAVILY_ARMOR_FLAT_DAMAGE_REDUCTION} flat reduced damage, and have {gc.HEAVILY_ARMOR_PERCENT_DAMAGE_REDUCTION}% damage reduction (after flat reduction). Maximum damage reduction is capped at {gc.MAX_HEAVILY_ARMOR_DAMAGE_REDUCTION}%. Also see <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a>.",
    GlossaryEntryType.HUNTER: "While most units target the nearest enemy unit, Hunters prioritize units with low current health.",
    GlossaryEntryType.POISON: "Poison damage is dealt over 2 seconds, and is not blocked by armor. Projectiles that poison pass through units that are already poisoned.",
    GlossaryEntryType.INFECTION: f"Infected units turn into <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> when they die. Infection lasts for 2 seconds.",
    GlossaryEntryType.KILLING_BLOW: "A killing blow is when an instance of damage is enough to kill a unit. Some units have special abilities that trigger when they deal a killing blow.",
    GlossaryEntryType.POINTS: f"Points represent the value of a unit. When you have more than {gc.CORRUPTION_TRIGGER_POINTS} points of units in your <a href='{GlossaryEntryType.BARRACKS.value}'>Barracks</a>, <a href='{GlossaryEntryType.CORRUPTION.value}'>Corruption</a> will trigger.",
    GlossaryEntryType.SPREADER: f"While most units target the nearest enemy unit, Spreaders prioritize units that are not <a href='{GlossaryEntryType.INFECTION.value}'>Infected</a>.",
    GlossaryEntryType.UPGRADE: "Units come in three tiers: Basic, Advanced and Elite. All units start as Basic. You can find special upgrade hexes to promote your units from Basic to Advanced. To promote a unit to Elite, one of your upgrade hexes must be <a href='{GlossaryEntryType.CORRUPTION.value}'>Corrupted</a>. Enemy units start as Basic, but become Elite when they are <a href='{GlossaryEntryType.CORRUPTION.value}'>Corrupted</a>."
}

# Upgrade descriptions for each unit type
UPGRADE_DESCRIPTIONS = {
    UnitType.CORE_ARCHER: {
        UnitTier.ADVANCED: "50% increased attack speed",
        UnitTier.ELITE: "50% increased range\n50% increased projectile speed"
    },
    UnitType.CORE_BARBARIAN: {
        UnitTier.ADVANCED: "25% increased health and damage",
        UnitTier.ELITE: "25% increased movement and attack speed"
    },
    UnitType.CORE_CAVALRY: {
        UnitTier.ADVANCED: "60% increased health",
        UnitTier.ELITE: "60% increased damage"
    },
    UnitType.CORE_DUELIST: {
        UnitTier.ADVANCED: "50% increased hits per combo",
        UnitTier.ELITE: "50% increased hits per combo"
    },
    UnitType.CORE_LONGBOWMAN: {
        UnitTier.ADVANCED: "Arrows pierce through one target\n33% reduced damage",
        UnitTier.ELITE: "Damage restored to 100%"
    },
    UnitType.CORE_SWORDSMAN: {
        UnitTier.ADVANCED: "30% increased health and damage",
        UnitTier.ELITE: "30% increased health and damage"
    },
    UnitType.CORE_WIZARD: {
        UnitTier.ADVANCED: "50% increased damage",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.CRUSADER_BANNER_BEARER: {
        UnitTier.ADVANCED: "50% increased health\nAura grants 25% increased damage",
        UnitTier.ELITE: "50% increased health\nAura grants 25% increased attack speed"
    },
    UnitType.CRUSADER_BLACK_KNIGHT: {
        UnitTier.ADVANCED: "30% increased health and movement speed",
        UnitTier.ELITE: "60% increased damage"
    },
    UnitType.CRUSADER_CATAPULT: {
        UnitTier.ADVANCED: "25% increased health and damage",
        UnitTier.ELITE: "25% reduced minimum range"
    },
    UnitType.CRUSADER_CLERIC: {
        UnitTier.ADVANCED: "100% increased range",
        UnitTier.ELITE: "50% increased attack speed"
    },
    UnitType.CRUSADER_COMMANDER: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.CRUSADER_CROSSBOWMAN: {
        UnitTier.ADVANCED: "Gains Heavily Armored",
        UnitTier.ELITE: "25% increased damage and attack speed"
    },
    UnitType.CRUSADER_DEFENDER: {
        UnitTier.ADVANCED: "Gains Heavily Armored\n25% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.CRUSADER_GOLD_KNIGHT: {
        UnitTier.ADVANCED: "20% increased health, damage, and healing",
        UnitTier.ELITE: "20% increased health, damage, and healing"
    },
    UnitType.CRUSADER_GUARDIAN_ANGEL: {
        UnitTier.ADVANCED: "50% increased healing",
        UnitTier.ELITE: "50% increased healing"
    },
    UnitType.CRUSADER_PALADIN: {
        UnitTier.ADVANCED: "100% increased damage",
        UnitTier.ELITE: "25% increased movement and attack speed"
    },
    UnitType.CRUSADER_PIKEMAN: {
        UnitTier.ADVANCED: "30% increased damage\n15% increased health",
        UnitTier.ELITE: "30% increased damage\n15% increased health"
    },
    UnitType.CRUSADER_RED_KNIGHT: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.CRUSADER_SOLDIER: {
        UnitTier.ADVANCED: "20% increased health, damage, and range",
        UnitTier.ELITE: "20% increased health, damage, and range"
    },
    UnitType.ZOMBIE_BASIC_ZOMBIE: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.ZOMBIE_BRUTE: {
        UnitTier.ADVANCED: "25% increased health and damage",
        UnitTier.ELITE: "25% increased health and damage"
    },
    UnitType.ZOMBIE_GRABBER: {
        UnitTier.ADVANCED: "50% increased health and damage",
        UnitTier.ELITE: "50% increased health and damage"
    },
    UnitType.ZOMBIE_JUMPER: {
        UnitTier.ADVANCED: "30% increased health\n15% increased movement and attack speed",
        UnitTier.ELITE: "30% increased health\n15% increased movement and attack speed"
    },
    UnitType.ZOMBIE_SPITTER: {
        UnitTier.ADVANCED: "50% increased damage",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.ZOMBIE_TANK: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.WEREBEAR: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    }
}

def get_upgrade_description(unit_type: UnitType, unit_tier: UnitTier) -> str:
    """Get the upgrade description for a specific unit type and tier."""
    if unit_type not in UPGRADE_DESCRIPTIONS:
        return ""
    
    tier_descriptions = UPGRADE_DESCRIPTIONS[unit_type]
    return tier_descriptions.get(unit_tier, "")

def get_unit_data(unit_type: UnitType, unit_tier: UnitTier = UnitTier.BASIC) -> UnitData:
    """Get unit data for the specified unit type and tier."""
    
    # Define base unit data with tier-specific calculations
    base_unit_data = {}
    
    if unit_type == UnitType.CORE_ARCHER:
        # Calculate tier-specific values
        archer_damage = gc.CORE_ARCHER_ATTACK_DAMAGE
        attack_range = gc.CORE_ARCHER_ATTACK_RANGE
        attack_animation_duration = gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION
        projectile_speed = gc.CORE_ARCHER_PROJECTILE_SPEED
        
        # Advanced tier: 50% faster rate of fire
        if unit_tier == UnitTier.ADVANCED:
            attack_animation_duration = attack_animation_duration * 2/3  # 50% faster = 2/3 duration
        
        # Elite tier: 50% more range, 50% more projectile speed, AND keeps the faster rate of fire from Advanced
        elif unit_tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 2/3  # Keep Advanced upgrade
            attack_range = attack_range * 1.5  # Add Elite range upgrade
            projectile_speed = projectile_speed * 1.5  # Add Elite projectile speed upgrade
            
        return UnitData(
            name="Archer",
            description="Archers are basic ranged units that can target units from afar.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_ARCHER_HP),
                StatType.SPEED: speed_stat(gc.CORE_ARCHER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(archer_damage / attack_animation_duration),
                StatType.RANGE: range_stat(attack_range),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_ARCHER_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_ARCHER_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: f"{archer_damage:.0f} per hit ({archer_damage / attack_animation_duration:.1f} per second)" + (f". Projectile speed: {projectile_speed:.0f}" if unit_tier == UnitTier.ELITE else ""),
                StatType.RANGE: f"{attack_range:.0f} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against slow melee units", "In a large group", "Behind other units"],
                "Weak when": ["Against fast units", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CORE_BARBARIAN:
        # Calculate tier-specific values
        barbarian_health = gc.CORE_BARBARIAN_HP
        barbarian_damage = gc.CORE_BARBARIAN_ATTACK_DAMAGE
        barbarian_movement_speed = gc.CORE_BARBARIAN_MOVEMENT_SPEED
        attack_animation_duration = gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION
        
        # Advanced tier (and Elite): 25% more health and damage
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            barbarian_health = barbarian_health * 1.25
            barbarian_damage = barbarian_damage * 1.25
        
        # Elite tier: additional 25% faster movement speed and attack speed
        if unit_tier == UnitTier.ELITE:
            barbarian_movement_speed = barbarian_movement_speed * 1.25
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return UnitData(
            name="Barbarian",
            description=f"Barbarians are durable melee units that deal damage in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(barbarian_health),
                StatType.SPEED: speed_stat(barbarian_movement_speed),
                StatType.DAMAGE: damage_stat(barbarian_damage / attack_animation_duration, 1.5),
                StatType.RANGE: range_stat(gc.CORE_BARBARIAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{barbarian_health:.0f} maximum health",
                StatType.SPEED: f"{barbarian_movement_speed:.0f} units per second",
                StatType.DAMAGE: f"{barbarian_damage:.0f} per hit ({barbarian_damage / attack_animation_duration:.1f} per second) in a medium area",
                StatType.RANGE: f"{gc.CORE_BARBARIAN_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against groups of units", "In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "In one-on-one combat with stronger units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CORE_CAVALRY:
        # Calculate tier-specific values
        cavalry_health = gc.CORE_CAVALRY_HP
        cavalry_damage = gc.CORE_CAVALRY_ATTACK_DAMAGE
        
        # Advanced tier: 60% more health
        if unit_tier == UnitTier.ADVANCED:
            cavalry_health = cavalry_health * 1.6
        
        # Elite tier: another +60% HP (total 2.2x base health)
        elif unit_tier == UnitTier.ELITE:
            cavalry_health = cavalry_health * 2.2
        
        return UnitData(
            name="Cavalry",
            description="Cavalry are fast and durable, but have low damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(cavalry_health),
                StatType.SPEED: speed_stat(gc.CORE_CAVALRY_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(cavalry_damage / gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_CAVALRY_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{cavalry_health:.0f} maximum health",
                StatType.SPEED: f"{gc.CORE_CAVALRY_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{cavalry_damage:.0f} per hit ({cavalry_damage / gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_CAVALRY_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against ranged units", "With other fast units", "Tanking damage"],
                "Weak when": ["Against stronger melee units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CORE_DUELIST:
        duelist_damage = gc.CORE_DUELIST_ATTACK_DAMAGE
        if unit_tier == UnitTier.BASIC:
            hit_multiplier = 2
        elif unit_tier == UnitTier.ADVANCED:
            hit_multiplier = 3
        elif unit_tier == UnitTier.ELITE:
            hit_multiplier = 4
        
        return UnitData(
            name="Duelist",
            description="Duelists are fragile melee units that attack many times quickly.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_DUELIST_HP),
                StatType.SPEED: speed_stat(gc.CORE_DUELIST_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(duelist_damage * hit_multiplier * 7/ gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_DUELIST_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_DUELIST_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_DUELIST_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{duelist_damage} per hit ({duelist_damage * hit_multiplier * 7 / gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_DUELIST_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against high health units", "In a large group", "Behind other units"],
                "Weak when": ["Against ranged units", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CORE_LONGBOWMAN:
        longbowman_damage = gc.CORE_LONGBOWMAN_ATTACK_DAMAGE
        attack_animation_duration = gc.CORE_LONGBOWMAN_ANIMATION_ATTACK_DURATION
        
        # Advanced tier: 33.33% damage cut
        if unit_tier == UnitTier.ADVANCED:
            longbowman_damage = longbowman_damage * (2/3)  # 33.33% damage cut
        
        # Elite tier: damage back to normal (no damage cut, no attack speed bonus)
        # No additional changes needed since longbowman_damage starts at base value
        
        # Advanced and Elite: Arrows pierce one target
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            description = f"Longbowmen are ranged units that shoot powerful piercing arrows over very long range."
        else:
            description = "Longbowmen are ranged units that shoot powerful arrows over very long range."
        
        return UnitData(
            name="Longbowman",
            description=description,
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_LONGBOWMAN_HP),
                StatType.DAMAGE: damage_stat(longbowman_damage / attack_animation_duration, 1.5 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 1),
                StatType.RANGE: range_stat(gc.CORE_LONGBOWMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CORE_LONGBOWMAN_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_LONGBOWMAN_HP} maximum health",
                StatType.DAMAGE: f"{longbowman_damage:.0f} per hit ({longbowman_damage / attack_animation_duration:.1f} per second)" + (". Arrows pierce one target." if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else ""),
                StatType.RANGE: f"{gc.CORE_LONGBOWMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CORE_LONGBOWMAN_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against other ranged units", "Against slow melee units", "Against healing units", "When hitting multiple targets with one arrow"],
                "Weak when": ["Against fast melee units"],
            },
            modification_levels={
                StatType.DAMAGE: 2 if unit_tier == UnitTier.ELITE else 1 if unit_tier == UnitTier.ADVANCED else 0,
                StatType.RANGE: 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CORE_SWORDSMAN:
        # Calculate tier-specific values
        swordsman_damage = gc.CORE_SWORDSMAN_ATTACK_DAMAGE
        swordsman_health = gc.CORE_SWORDSMAN_HP
        
        # Advanced tier: 30% more health and damage
        if unit_tier == UnitTier.ADVANCED:
            swordsman_damage = swordsman_damage * 1.3
            swordsman_health = swordsman_health * 1.3
        
        # Elite tier: 60% more health and damage (total)
        elif unit_tier == UnitTier.ELITE:
            swordsman_damage = swordsman_damage * 1.6
            swordsman_health = swordsman_health * 1.6
        
        return UnitData(
            name="Swordsman",
            description="Swordsmen are balanced melee units that deal high damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(swordsman_health),
                StatType.SPEED: speed_stat(gc.CORE_SWORDSMAN_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(swordsman_damage / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_SWORDSMAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(swordsman_health)} maximum health",
                StatType.SPEED: f"{gc.CORE_SWORDSMAN_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{int(swordsman_damage)} per hit ({swordsman_damage / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_SWORDSMAN_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against high health units", "Against weaker melee units", "In a large group"],
                "Weak when": ["Against ranged units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CORE_WIZARD:
        # Calculate tier-specific damage
        wizard_damage = gc.CORE_WIZARD_ATTACK_DAMAGE
        
        # Advanced tier: 50% more damage
        if unit_tier == UnitTier.ADVANCED:
            wizard_damage = wizard_damage * 1.5
        
        # Elite tier: 100% more damage total
        elif unit_tier == UnitTier.ELITE:
            wizard_damage = wizard_damage * 2.0
        
        return UnitData(
            name="Wizard",
            description=f"Wizards shoot fireballs that damage allied and enemy units in a large <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_WIZARD_HP),
                StatType.SPEED: speed_stat(gc.CORE_WIZARD_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(wizard_damage / gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION, 2),
                StatType.RANGE: range_stat(gc.CORE_WIZARD_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_WIZARD_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_WIZARD_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{int(wizard_damage)} per hit ({wizard_damage / gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION:.1f} per second) in a large area",
                StatType.RANGE: f"{gc.CORE_WIZARD_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against large groups", "Against slow units"],
                "Weak when": ["Against fast melee units", "Allies are in the way", "Against high health units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_BANNER_BEARER:
        banner_bearer_health = gc.CRUSADER_BANNER_BEARER_HP
        if unit_tier == UnitTier.ADVANCED:
            banner_bearer_health = gc.CRUSADER_BANNER_BEARER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            banner_bearer_health = gc.CRUSADER_BANNER_BEARER_HP * 2.0
        
        # Generate tier-specific utility tooltip
        utility_description = f"Aura sets ally movement speed to {gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second"
        
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            utility_description += f" and grants +{int(gc.CRUSADER_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE * 100)}% damage"
        
        if unit_tier == UnitTier.ELITE:
            utility_description += " and +25% attack speed"
        
        utility_description += f" in a radius of {gc.CRUSADER_BANNER_BEARER_AURA_RADIUS}"
        
        # Generate tier-specific description
        if unit_tier == UnitTier.BASIC:
            description = f"Banner Bearers are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> with an <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts ally movement speed."
        elif unit_tier == UnitTier.ADVANCED:
            description = f"Banner Bearers are hardy <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> with an <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts ally movement speed and damage."
        else:  # Elite
            description = f"Banner Bearers are elite <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> with a powerful <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts ally movement speed, damage, and attack speed."
        
        return UnitData(
            name="Banner Bearer",
            description=description,
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(banner_bearer_health),
                StatType.SPEED: speed_stat(gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED),
                StatType.UTILITY: 6 if unit_tier == UnitTier.BASIC else 12 if unit_tier == UnitTier.ADVANCED else 18,
                StatType.DAMAGE: None,
                StatType.RANGE: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(banner_bearer_health)} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: utility_description,
                StatType.DAMAGE: None,
                StatType.RANGE: None
            },
            tips={
                "Strong when": ["In a large group", "With slow allies", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
                "Weak when": [f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 0,
                StatType.RANGE: 0,
                StatType.SPEED: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_BLACK_KNIGHT:
        # Calculate tier-specific values
        black_knight_health = gc.CRUSADER_BLACK_KNIGHT_HP
        black_knight_movement_speed = gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED
        black_knight_damage = gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE
        
        # Advanced tier (and Elite): 30% more health and speed
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            black_knight_health = black_knight_health * 1.3
            black_knight_movement_speed = black_knight_movement_speed * 1.3
        
        # Elite tier: 60% more damage
        if unit_tier == UnitTier.ELITE:
            black_knight_damage = black_knight_damage * 1.6
        
        return UnitData(
            name="Black Knight",
            description=f"Black Knights are fast, <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that cause nearby units to <a href='{GlossaryEntryType.FLEE.value}'>Flee</a> on <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blows</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(black_knight_health, armored=True),
                StatType.SPEED: speed_stat(black_knight_movement_speed),
                StatType.DAMAGE: damage_stat(black_knight_damage / gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION),
                StatType.UTILITY: 7,
                StatType.RANGE: range_stat(gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{int(black_knight_health)} maximum health, armored",
                StatType.SPEED: f"{black_knight_movement_speed:.1f} units per second",
                StatType.DAMAGE: f"{int(black_knight_damage)} per hit ({black_knight_damage / gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.UTILITY: "Nearby units flee on killing blow",
                StatType.RANGE: f"{gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE} units"
            },
            tips={
                "Strong when": ["Against low health units", "Able to kill multiple units quickly", "Against units with low damage per hit"],
                "Weak when": ["Walking through enemies to get to targets", "Against stronger melee units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_CATAPULT:
        # Calculate tier-specific values
        catapult_health = gc.CRUSADER_CATAPULT_HP
        catapult_damage = gc.CRUSADER_CATAPULT_DAMAGE
        catapult_min_range = gc.CRUSADER_CATAPULT_MINIMUM_RANGE
        catapult_max_range = gc.CRUSADER_CATAPULT_MAXIMUM_RANGE
        
        # Advanced tier (and Elite): 25% more health and damage
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            catapult_health = catapult_health * 1.25
            catapult_damage = catapult_damage * 1.25
        
        # Elite tier: 25% reduced minimum range only
        if unit_tier == UnitTier.ELITE:
            catapult_min_range = catapult_min_range * 0.75
        
        return UnitData(
            name="Catapult",
            description=f"Catapults are immobile ranged units that deal high damage to all units in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(catapult_health),
                StatType.DAMAGE: damage_stat(catapult_damage / gc.CRUSADER_CATAPULT_COOLDOWN, 3),
                StatType.RANGE: range_stat(catapult_max_range),
                StatType.SPEED: None,
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(catapult_health)} maximum health",
                StatType.DAMAGE: f"{int(catapult_damage)} per hit ({catapult_damage / gc.CRUSADER_CATAPULT_COOLDOWN:.1f} per second) in a medium area",
                StatType.RANGE: f"Between {int(catapult_min_range)} and {int(catapult_max_range)} units",
                StatType.SPEED: None,
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against clustered groups", "Against slow units"],
                "Weak when": ["Against fast units", "Against spread out units", "Enemy units are too close", "Allies are in the way"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_CLERIC:
        # Calculate tier-specific values
        cleric_range = gc.CRUSADER_CLERIC_ATTACK_RANGE
        cleric_animation_duration = gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION
        
        # Advanced tier (and Elite): 100% increased range
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            cleric_range = cleric_range * 2.0
        
        # Elite tier: 50% faster casting speed
        if unit_tier == UnitTier.ELITE:
            cleric_animation_duration = cleric_animation_duration * 2/3  # 50% faster = 2/3 duration
        
        return UnitData(
            name="Healer",
            description=f"Healers are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> that heal the most damaged ally in range.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CRUSADER_CLERIC_HP),
                StatType.SPEED: speed_stat(gc.CRUSADER_CLERIC_MOVEMENT_SPEED),
                StatType.UTILITY: healing_stat(gc.CRUSADER_CLERIC_HEALING / cleric_animation_duration),
                StatType.RANGE: range_stat(cleric_range),
                StatType.DAMAGE: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CRUSADER_CLERIC_HP} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_CLERIC_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: f"{gc.CRUSADER_CLERIC_HEALING} health per cast, {gc.CRUSADER_CLERIC_HEALING / cleric_animation_duration:.1f} per second",
                StatType.RANGE: f"{int(cleric_range)} units",
                StatType.DAMAGE: None
            },
            tips={
                "Strong when": ["In a large group", f"Allies are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a>", "Against units with low damage per second"],
                "Weak when": ["Against units with high damage per second", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
            },
            modification_levels={
                StatType.RANGE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.DAMAGE: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_COMMANDER:
        commander_health = gc.CRUSADER_COMMANDER_HP
        if unit_tier == UnitTier.ADVANCED:
            commander_health = gc.CRUSADER_COMMANDER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            commander_health = gc.CRUSADER_COMMANDER_HP * 2.0
        
        return UnitData(
            name="Commander",
            description=f"Commanders are support units with an <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(commander_health),
                StatType.SPEED: speed_stat(gc.CRUSADER_COMMANDER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_COMMANDER_ATTACK_DAMAGE / gc.CRUSADER_COMMANDER_ANIMATION_ATTACK_DURATION),
                StatType.UTILITY: 6,
                StatType.RANGE: range_stat(gc.CRUSADER_COMMANDER_ATTACK_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{commander_health} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_COMMANDER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.CRUSADER_COMMANDER_ATTACK_DAMAGE} per hit ({gc.CRUSADER_COMMANDER_ATTACK_DAMAGE / gc.CRUSADER_COMMANDER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.UTILITY: f"Aura grants +{int(gc.CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE * 100)}% damage to allies in a radius of {gc.CRUSADER_COMMANDER_AURA_RADIUS}",
                StatType.RANGE: f"{gc.CRUSADER_COMMANDER_ATTACK_RANGE} units"
            },
            tips={
                "Strong when": ["In a large group", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
                "Weak when": [f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>", "When allies are too far away"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_CROSSBOWMAN:
        # Calculate tier-specific values
        crossbowman_health = gc.CRUSADER_CROSSBOWMAN_HP
        crossbowman_damage = gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE
        crossbowman_attack_duration = gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION
        crossbowman_reload_duration = gc.CRUSADER_CROSSBOWMAN_ANIMATION_RELOAD_DURATION
        crossbowman_armored = True
        crossbowman_heavily_armored = False
        description = f"Crossbowmen are medium-ranged <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that need to reload."
        defense_tooltip = f"{crossbowman_health} maximum health, armored"
        
        # Advanced tier (and Elite): Gains heavy armor
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            crossbowman_heavily_armored = True
            crossbowman_armored = False
            description = f"Crossbowmen are medium-ranged <a href='{GlossaryEntryType.HEAVILY_ARMORED.value}'>Heavily Armored</a> units that need to reload."
            defense_tooltip = f"{crossbowman_health} maximum health, heavily armored"
        
        # Elite tier: 25% increased damage and attack speed, and 25% faster reload
        if unit_tier == UnitTier.ELITE:
            crossbowman_damage = crossbowman_damage * 1.25
            crossbowman_attack_duration = crossbowman_attack_duration * 0.8  # 25% faster = 0.8x duration
            crossbowman_reload_duration = crossbowman_reload_duration * 0.8  # 25% faster = 0.8x duration
        
        return UnitData(
            name="Crossbowman",
            description=description,
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(crossbowman_health, armored=crossbowman_armored, heavily_armored=crossbowman_heavily_armored),
                StatType.DAMAGE: damage_stat(crossbowman_damage / (crossbowman_attack_duration + crossbowman_reload_duration/2)),
                StatType.RANGE: range_stat(gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_CROSSBOWMAN_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: defense_tooltip,
                StatType.DAMAGE: f"{crossbowman_damage} per hit ({crossbowman_damage / crossbowman_attack_duration:.1f} per second while attacking, {crossbowman_damage / (crossbowman_attack_duration + crossbowman_reload_duration/2):.1f} per second including reloading). Starts with {gc.CRUSADER_CROSSBOWMAN_STARTING_AMMO} ammo, and can reload to regain ammo, up to {gc.CRUSADER_CROSSBOWMAN_MAX_AMMO}.",
                StatType.RANGE: f"{gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_CROSSBOWMAN_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to reload between fights", "Against units with low health", "In a large group", "Against units with low damage per hit"],
                "Weak when": ["Against long-ranged units", "Against fast units", "Reloading"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_DEFENDER:
        # Calculate tier-specific values
        defender_health = gc.CRUSADER_DEFENDER_HP
        defender_armored = True
        defender_heavily_armored = False
        description = f"Defenders are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units with high health and low damage."
        defense_tooltip = f"{defender_health} maximum health, armored"

        # Advanced tier: 25% more health
        if unit_tier == UnitTier.ADVANCED:
            defender_health = defender_health * 1.25
            
        # Elite tier: 75% more health total
        elif unit_tier == UnitTier.ELITE:
            defender_health = defender_health * 1.75
        
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            defender_heavily_armored = True
            defender_armored = False
            description = f"Defenders are <a href='{GlossaryEntryType.HEAVILY_ARMORED.value}'>Heavily Armored</a> units with high health and low damage."
            defense_tooltip = f"{int(defender_health)} maximum health, heavily armored"
        
        return UnitData(
            name="Defender",
            description=description,
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(defender_health, armored=defender_armored, heavily_armored=defender_heavily_armored),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_DEFENDER_ATTACK_DAMAGE / gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_DEFENDER_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_DEFENDER_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: defense_tooltip,
                StatType.DAMAGE: f"{gc.CRUSADER_DEFENDER_ATTACK_DAMAGE} per hit ({gc.CRUSADER_DEFENDER_ATTACK_DAMAGE / gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_DEFENDER_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_DEFENDER_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Tanking damage", "Against units with low damage per hit", "Supported by healing units"],
                "Weak when": ["Against more powerful melee units", "Against ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_GOLD_KNIGHT:
        # Calculate tier-specific values
        gold_knight_health = gc.CRUSADER_GOLD_KNIGHT_HP
        gold_knight_damage = gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE
        gold_knight_healing = gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL
        
        # Advanced tier: 20% increased damage, healing, and health
        if unit_tier == UnitTier.ADVANCED:
            gold_knight_health = gold_knight_health * 1.2
            gold_knight_damage = gold_knight_damage * 1.2
            gold_knight_healing = gold_knight_healing * 1.2
        
        # Elite tier: 40% increased damage, healing, and health (total)
        elif unit_tier == UnitTier.ELITE:
            gold_knight_health = gold_knight_health * 1.4
            gold_knight_damage = gold_knight_damage * 1.4
            gold_knight_healing = gold_knight_healing * 1.4
        
        return UnitData(
            name="Gold Knight",
            description=f"Gold Knights are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units with very fast <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> attacks that heal per enemy hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gold_knight_health, armored=True, self_heal_dps=gold_knight_healing / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION * 1.5),
                StatType.SPEED: speed_stat(gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gold_knight_damage / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION, 1.5),
                StatType.RANGE: range_stat(gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gold_knight_health} maximum health, armored. Heals {gold_knight_healing} per enemy hit ({gold_knight_healing / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per enemy per second)",
                StatType.SPEED: f"{gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gold_knight_damage} per hit, {gold_knight_damage / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second in a medium area",
                StatType.RANGE: f"{gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against melee units","Against large groups", "Against units with low damage per hit", "Supported by healing units", "Spreading out incoming damage"],
                "Weak when": ["Against ranged units", "Against stronger melee units", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units", "Overwhelmed by high damage"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_GUARDIAN_ANGEL:
        # Calculate tier-specific healing
        guardian_angel_healing = gc.CRUSADER_GUARDIAN_ANGEL_HEALING
        
        # Advanced tier: 50% increased healing
        if unit_tier == UnitTier.ADVANCED:
            guardian_angel_healing = guardian_angel_healing * 1.5
        
        # Elite tier: 100% increased healing (total)
        elif unit_tier == UnitTier.ELITE:
            guardian_angel_healing = guardian_angel_healing * 2.0
        
        return UnitData(
            name="Guardian Angel",
            description=f"Guardian Angels are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> that continuously heal the ally they are following.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CRUSADER_GUARDIAN_ANGEL_HP),
                StatType.SPEED: speed_stat(gc.CRUSADER_GUARDIAN_ANGEL_MOVEMENT_SPEED),
                StatType.UTILITY: healing_stat(guardian_angel_healing / gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN),
                StatType.RANGE: range_stat(gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE),
                StatType.DAMAGE: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CRUSADER_GUARDIAN_ANGEL_HP} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_GUARDIAN_ANGEL_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: f"{guardian_angel_healing} health per cast, {guardian_angel_healing / gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN:.1f} per second",
                StatType.RANGE: f"{gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE} units",
                StatType.DAMAGE: None
            },
            tips={
                "Strong when": [f"Supporting an <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> unit", "Supporting ally against a single low-damage enemy"],
                "Weak when": [f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>", "Following a unit that is full health"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.DAMAGE: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_PALADIN:
        # Calculate tier-specific values
        paladin_damage = gc.CRUSADER_PALADIN_ATTACK_DAMAGE
        paladin_movement_speed = gc.CRUSADER_PALADIN_MOVEMENT_SPEED
        paladin_attack_animation_duration = gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION
        
        # Advanced tier (and Elite): 100% increased damage
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            paladin_damage = paladin_damage * 2.0
        
        # Elite tier: 25% increased movement speed and 25% faster attack animation
        if unit_tier == UnitTier.ELITE:
            paladin_movement_speed = paladin_movement_speed * 1.25
            paladin_attack_animation_duration = paladin_attack_animation_duration * 0.8  # 25% faster
        
        return UnitData(
            name="Paladin",
            description=f"Paladins are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can heal themselves.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CRUSADER_PALADIN_HP, self_heal_dps=gc.CRUSADER_PALADIN_SKILL_HEAL / gc.CRUSADER_PALADIN_SKILL_COOLDOWN, armored=True),
                StatType.DAMAGE: damage_stat(paladin_damage / paladin_attack_animation_duration),
                StatType.RANGE: range_stat(gc.CRUSADER_PALADIN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(paladin_movement_speed),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CRUSADER_PALADIN_HP} maximum health, armored. Heals for {gc.CRUSADER_PALADIN_SKILL_HEAL} per cast ({gc.CRUSADER_PALADIN_SKILL_HEAL / gc.CRUSADER_PALADIN_SKILL_COOLDOWN:.1f} per second)",
                StatType.DAMAGE: f"{paladin_damage} per hit ({paladin_damage / paladin_attack_animation_duration:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_PALADIN_ATTACK_RANGE} units",
                StatType.SPEED: f"{paladin_movement_speed} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Tanking damage", "Against units with low damage per hit", "In one-on-one fights", "Supported by healing units"],
                "Weak when": ["Against units with high damage per hit", "Against units with high damage per second", "Against large groups"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_PIKEMAN:
        # Calculate tier-specific values
        pikeman_health = gc.CRUSADER_PIKEMAN_HP
        pikeman_damage = gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE
        
        # Advanced tier: 30% increased damage, 15% increased health
        if unit_tier == UnitTier.ADVANCED:
            pikeman_damage = pikeman_damage * 1.3
            pikeman_health = pikeman_health * 1.15
        
        # Elite tier: 60% increased damage total, 30% increased health total
        elif unit_tier == UnitTier.ELITE:
            pikeman_damage = pikeman_damage * 1.6
            pikeman_health = pikeman_health * 1.3
        
        return UnitData(
            name="Pikeman",
            description=f"Pikemen are melee units with high damage and long reach.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(pikeman_health),
                StatType.DAMAGE: damage_stat(pikeman_damage / gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_PIKEMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{pikeman_health:.0f} maximum health",
                StatType.DAMAGE: f"{pikeman_damage:.0f} per hit ({pikeman_damage / gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_PIKEMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": [f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units", "In a large group", "Behind other units"],
                "Weak when": ["Against ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_RED_KNIGHT:
        red_knight_health = gc.CRUSADER_RED_KNIGHT_HP
        if unit_tier == UnitTier.ADVANCED:
            red_knight_health = gc.CRUSADER_RED_KNIGHT_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            red_knight_health = gc.CRUSADER_RED_KNIGHT_HP * 2.0
        
        return UnitData(
            name="Red Knight",
            description=f"Red Knights are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can switch between melee and ranged attacks.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(red_knight_health, armored=True),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_RED_KNIGHT_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE),    
                StatType.SPEED: speed_stat(gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{red_knight_health} maximum health, armored",
                StatType.DAMAGE: f"{gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE} per hit ({gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_RED_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["TODO"],
                "Weak when": ["TODO"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_SOLDIER:
        # Calculate tier-specific values
        soldier_health = gc.CRUSADER_SOLDIER_HP
        soldier_melee_damage = gc.CRUSADER_SOLDIER_MELEE_DAMAGE
        soldier_ranged_damage = gc.CORE_ARCHER_ATTACK_DAMAGE
        soldier_ranged_range = gc.CRUSADER_SOLDIER_RANGED_RANGE
        
        # Advanced tier: 20% increased health, damage, and range (bow only)
        if unit_tier == UnitTier.ADVANCED:
            soldier_health = soldier_health * 1.2
            soldier_melee_damage = soldier_melee_damage * 1.2
            soldier_ranged_damage = soldier_ranged_damage * 1.2
            soldier_ranged_range = soldier_ranged_range * 1.2
        
        # Elite tier: 40% increased health, damage, and range (bow only) total
        elif unit_tier == UnitTier.ELITE:
            soldier_health = soldier_health * 1.4
            soldier_melee_damage = soldier_melee_damage * 1.4
            soldier_ranged_damage = soldier_ranged_damage * 1.4
            soldier_ranged_range = soldier_ranged_range * 1.4
        
        return UnitData(
            name="Soldier",
            description=f"Soliders are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can switch between melee and ranged attacks.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(soldier_health, armored=True),
                StatType.DAMAGE: damage_stat(soldier_melee_damage / gc.CRUSADER_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION),
                StatType.RANGE: range_stat(soldier_ranged_range),
                StatType.SPEED: speed_stat(gc.CRUSADER_SOLDIER_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{soldier_health:.0f} maximum health, armored",
                StatType.DAMAGE: f"Melee: {soldier_melee_damage:.0f} per hit ({soldier_melee_damage / gc.CRUSADER_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION:.1f} per second), Ranged: {soldier_ranged_damage:.0f} per hit ({soldier_ranged_damage / gc.CRUSADER_SOLDIER_ANIMATION_RANGED_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"Melee: {gc.CRUSADER_SOLDIER_MELEE_RANGE} units, Ranged: {soldier_ranged_range:.0f} units",
                StatType.SPEED: f"{gc.CRUSADER_SOLDIER_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Can weaken melee enemies with ranged attacks", "Against units with low damage per hit"],
                "Weak when": ["Against stronger melee units or ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    if unit_type == UnitType.ZOMBIE_BASIC_ZOMBIE:
        zombie_basic_zombie_health = gc.ZOMBIE_BASIC_ZOMBIE_HP
        if unit_tier == UnitTier.ADVANCED:
            zombie_basic_zombie_health = gc.ZOMBIE_BASIC_ZOMBIE_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_basic_zombie_health = gc.ZOMBIE_BASIC_ZOMBIE_HP * 2.0
        
        return UnitData(
            name="Zombie",
            description=f"Zombies are slow, weak melee units that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_basic_zombie_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE / gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_basic_zombie_health} maximum health",    
                StatType.SPEED: f"{gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE} per hit ({gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE / gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["In a large group", "Against many weak enemies", "Tanking damage"],
                "Weak when": ["Against ranged units", "Against units with high damage per second", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    if unit_type == UnitType.ZOMBIE_BRUTE:
        # Calculate tier-specific values
        zombie_brute_health = gc.ZOMBIE_BRUTE_HP
        zombie_brute_damage = gc.ZOMBIE_BRUTE_ATTACK_DAMAGE
        
        # Advanced tier: 25% increased health and damage
        if unit_tier == UnitTier.ADVANCED:
            zombie_brute_health = zombie_brute_health * 1.25
            zombie_brute_damage = zombie_brute_damage * 1.25
        
        # Elite tier: 50% increased health and damage total
        elif unit_tier == UnitTier.ELITE:
            zombie_brute_health = zombie_brute_health * 1.5
            zombie_brute_damage = zombie_brute_damage * 1.5
        
        return UnitData(
            name="Brute",
            description=f"Brutes are slow melee units that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and carry two <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> into battle.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_brute_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_BRUTE_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(zombie_brute_damage / gc.ZOMBIE_BRUTE_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_BRUTE_ATTACK_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_brute_health:.0f} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_BRUTE_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{zombie_brute_damage:.0f} per hit ({zombie_brute_damage / gc.ZOMBIE_BRUTE_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.ZOMBIE_BRUTE_ATTACK_RANGE} units",
                StatType.UTILITY: "Infects enemies on hit, carries two Zombies into battle"
            },
            tips={
                "Strong when": ["Against many weak enemies", "In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "Against units with high damage per second", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_GRABBER:
        # Calculate tier-specific values
        zombie_grabber_health = gc.ZOMBIE_GRABBER_HP
        grab_damage = gc.ZOMBIE_GRABBER_GRAB_DAMAGE
        melee_damage = gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE
        
        # Advanced tier: 50% increased health and damage
        if unit_tier == UnitTier.ADVANCED:
            zombie_grabber_health = zombie_grabber_health * 1.5
            grab_damage = grab_damage * 1.5
            melee_damage = melee_damage * 1.5
        
        # Elite tier: 100% increased health and damage total
        elif unit_tier == UnitTier.ELITE:
            zombie_grabber_health = zombie_grabber_health * 2.0
            grab_damage = grab_damage * 2.0
            melee_damage = melee_damage * 2.0
        
        return UnitData(
            name="Grabber",
            description=f"Grabbers are slow melee units with long reach that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and can grab and pull enemies towards them.",
            tier=unit_tier,
            stats={ 
                StatType.DEFENSE: defense_stat(zombie_grabber_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_GRABBER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(melee_damage / gc.ZOMBIE_GRABBER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_GRABBER_GRAB_MAXIMUM_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_grabber_health:.0f} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_GRABBER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{melee_damage:.0f} per hit ({melee_damage / gc.ZOMBIE_GRABBER_ANIMATION_ATTACK_DURATION:.1f} per second), Grab deals {grab_damage:.0f} per hit with a {gc.ZOMBIE_GRABBER_GRAB_COOLDOWN} second cooldown",
                StatType.RANGE: f"Melee: {gc.ZOMBIE_GRABBER_ATTACK_RANGE} units, Grab: {gc.ZOMBIE_GRABBER_GRAB_MINIMUM_RANGE} to {gc.ZOMBIE_GRABBER_GRAB_MAXIMUM_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit, can grab and pull enemies towards them"
            },
            tips={
                "Strong when": ["Pulling enemy units into a group of allies", "In a large group", "Behind other units", "Against ranged units"],
                "Weak when": ["In one-on-one combat", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_JUMPER:
        # Calculate tier-specific values
        zombie_jumper_health = gc.ZOMBIE_JUMPER_HP
        zombie_jumper_movement_speed = gc.ZOMBIE_JUMPER_MOVEMENT_SPEED
        attack_animation_duration = gc.ZOMBIE_JUMPER_ANIMATION_ATTACK_DURATION
        
        # Advanced tier: 30% more health, 15% more movement speed, 15% faster action speed
        if unit_tier == UnitTier.ADVANCED:
            zombie_jumper_health = zombie_jumper_health * 1.3
            zombie_jumper_movement_speed = zombie_jumper_movement_speed * 1.15
            attack_animation_duration = attack_animation_duration / 1.15  # 15% faster
        
        # Elite tier: 60% more health total, 30% more movement speed total, 30% faster action speed total
        elif unit_tier == UnitTier.ELITE:
            zombie_jumper_health = zombie_jumper_health * 1.6
            zombie_jumper_movement_speed = zombie_jumper_movement_speed * 1.3
            attack_animation_duration = attack_animation_duration / 1.3  # 30% faster
        
        return UnitData(
            name="Jumper",
            description=f"Jumpers are fast, high damage <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and can jump to their target.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_jumper_health),
                StatType.SPEED: speed_stat(zombie_jumper_movement_speed) + 2,
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_JUMPER_ATTACK_DAMAGE / attack_animation_duration),
                StatType.RANGE: range_stat(gc.ZOMBIE_JUMPER_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            }, 
            tooltips={
                StatType.DEFENSE: f"{zombie_jumper_health:.0f} maximum health",
                StatType.SPEED: f"{zombie_jumper_movement_speed:.1f} units per second, can jump {gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE} units every {gc.ZOMBIE_JUMPER_JUMP_COOLDOWN} seconds",
                StatType.DAMAGE: f"{gc.ZOMBIE_JUMPER_ATTACK_DAMAGE} per hit ({gc.ZOMBIE_JUMPER_ATTACK_DAMAGE / attack_animation_duration:.1f} per second). Jump deals {gc.ZOMBIE_JUMPER_JUMP_DAMAGE} damage with a {gc.ZOMBIE_JUMPER_JUMP_COOLDOWN} second cooldown",
                StatType.RANGE: f"Melee: {gc.ZOMBIE_JUMPER_ATTACK_RANGE} units, Jump: {gc.ZOMBIE_JUMPER_MINIMUM_JUMP_RANGE} to {gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["Against individual weak enemies", "Enemies are distracted", "Against ranged units"],
                "Weak when": ["Against stronger melee units", "Against fast melee units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_SPITTER:
        # Calculate tier-specific values
        spitter_damage = gc.ZOMBIE_SPITTER_ATTACK_DAMAGE
        melee_damage = gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE
        
        # Advanced tier: 50% increased damage
        if unit_tier == UnitTier.ADVANCED:
            spitter_damage = spitter_damage * 1.5
            melee_damage = melee_damage * 1.5
        
        # Elite tier: 100% increased damage total
        elif unit_tier == UnitTier.ELITE:
            spitter_damage = spitter_damage * 2.0
            melee_damage = melee_damage * 2.0
        
        return UnitData(
            name="Spitter",
            description=f"Spitters are slow, short-ranged <a href='{GlossaryEntryType.SPREADER.value}'>Spreaders</a> that <a href='{GlossaryEntryType.POISON.value}'>Poison</a> and <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.ZOMBIE_SPITTER_HP),
                StatType.SPEED: speed_stat(gc.ZOMBIE_SPITTER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(spitter_damage / gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION, 2/3),
                StatType.RANGE: range_stat(gc.ZOMBIE_SPITTER_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            },
            tooltips={
                StatType.DEFENSE: f"{gc.ZOMBIE_SPITTER_HP:.0f} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_SPITTER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{spitter_damage:.0f} poison damage ({spitter_damage/gc.ZOMBIE_INFECTION_DURATION:.1f} damage per second per poison) ({spitter_damage / gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION:.1f} per second if poisoning multiple enemies). Melee: {melee_damage:.0f} per hit",
                StatType.RANGE: f"{gc.ZOMBIE_SPITTER_ATTACK_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["Against many weak enemies", "In a large group", "Behind other units"],
                "Weak when": ["Against melee units", "Against long ranged units", "Against a small number of units", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_TANK:
        # Calculate tier-specific health
        zombie_tank_health = gc.ZOMBIE_TANK_HP
        
        # Advanced tier: 50% increased health
        if unit_tier == UnitTier.ADVANCED:
            zombie_tank_health = zombie_tank_health * 1.5
        
        # Elite tier: 100% increased health total
        elif unit_tier == UnitTier.ELITE:
            zombie_tank_health = zombie_tank_health * 2.0
        
        return UnitData(
            name="Tank",
            description=f"Tanks are slow melee units with very high health that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_tank_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_TANK_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_TANK_ATTACK_DAMAGE / gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_TANK_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_tank_health:.0f} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_TANK_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_TANK_ATTACK_DAMAGE} per hit, {gc.ZOMBIE_TANK_ATTACK_DAMAGE / gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION:.1f} per second + infection",
                StatType.RANGE: f"{gc.ZOMBIE_TANK_ATTACK_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "Against units with high damage per second"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.WEREBEAR:
        werebear_health = gc.WEREBEAR_HP
        if unit_tier == UnitTier.ADVANCED:
            werebear_health = gc.WEREBEAR_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            werebear_health = gc.WEREBEAR_HP * 2.0
        
        return UnitData(
            name="Werebear",
            description="Test unit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(werebear_health),
                StatType.SPEED: speed_stat(gc.WEREBEAR_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.WEREBEAR_ATTACK_DAMAGE / gc.WEREBEAR_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.WEREBEAR_ATTACK_RANGE),
                StatType.UTILITY: 0
            },
            tooltips={
                StatType.DEFENSE: f"{werebear_health} maximum health",
                StatType.SPEED: f"{gc.WEREBEAR_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.WEREBEAR_ATTACK_DAMAGE} per hit ({gc.WEREBEAR_ATTACK_DAMAGE / gc.WEREBEAR_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.WEREBEAR_ATTACK_RANGE} units",
                StatType.UTILITY: f"TODO"
            },
            tips={
                "Strong when": ["TODO"],
                "Weak when": ["TODO"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    raise ValueError(f"Unknown unit type: {unit_type}")