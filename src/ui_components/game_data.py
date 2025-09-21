import enum
from components.unit_tier import UnitTier
from components.unit_type import UnitType
from entities.items import ItemType
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
    stat = (dps * multiplier) / (gc.INFANTRY_PIKEMAN_ATTACK_DAMAGE / gc.INFANTRY_PIKEMAN_ANIMATION_ATTACK_DURATION) * 5
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
    stat = (range / gc.INFANTRY_CATAPULT_MAXIMUM_RANGE) * 24
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
    REVIVE = "Revive"
    INFECTION = "Infection"
    KILLING_BLOW = "Killing Blow"
    POINTS = "Points"
    SPREADER = "Spreader"
    UPGRADE = "Upgrade"
    INVISIBLE = "Invisible"
    UNUSABLE_CORPSE = "Unusable Corpse"

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

@dataclass
class ItemData:
    """Data class representing item information including description and tips."""
    name: str
    description: str
    tips: Dict[str, List[str]]

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
    GlossaryEntryType.REVIVE: "Units that are being revived gain progress towards reviving. Units worth more points take proportionally longer to revive. All progress only lasts for 15 seconds. If progress towards reviving is added by multiple sources from the same team, they are added together. If they are from different teams, they cancel each other out. Revived units are fresh instances of the original unit, and do not inherit any effects which may linger on the corpse. Corruption powers affect revived units based on which team they are revived onto, not their original team.",
    GlossaryEntryType.INFECTION: f"Infected units turn into <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> when they die. Infection lasts for 2 seconds. Some units have <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> and do not turn into zombies.",
    GlossaryEntryType.KILLING_BLOW: "A killing blow is when an instance of damage is enough to kill a unit. Some units have special abilities that trigger when they deal a killing blow.",
    GlossaryEntryType.POINTS: f"Points represent the value of a unit. When you have more than {gc.CORRUPTION_TRIGGER_POINTS} points of units in your <a href='{GlossaryEntryType.BARRACKS.value}'>Barracks</a>, <a href='{GlossaryEntryType.CORRUPTION.value}'>Corruption</a> will trigger.",
    GlossaryEntryType.SPREADER: f"While most units target the nearest enemy unit, Spreaders prioritize units that are not <a href='{GlossaryEntryType.INFECTION.value}'>Infected</a>.",
    GlossaryEntryType.UPGRADE: "Units come in three tiers: Basic, Advanced and Elite. All units start as Basic. You can find special upgrade hexes to promote your units from Basic to Advanced. To promote a unit to Elite, one of your upgrade hexes must be <a href='{GlossaryEntryType.CORRUPTION.value}'>Corrupted</a>. Enemy units start as Basic, but become Elite when they are <a href='{GlossaryEntryType.CORRUPTION.value}'>Corrupted</a>.",
    GlossaryEntryType.INVISIBLE: "Invisible units cannot be targeted by allies or enemies. They become visible when they attack or use abilities.",
    GlossaryEntryType.UNUSABLE_CORPSE: "Units with Unusable Corpses cannot be <a href='{GlossaryEntryType.REVIVE.value}'>Revived</a> or turned into <a href='{GlossaryEntryType.INFECTION.value}'>Zombies</a> when they die."
}

# Upgrade descriptions for each unit type
UPGRADE_DESCRIPTIONS = {
    UnitType.CORE_ARCHER: {
        UnitTier.ADVANCED: "50% increased attack speed",
        UnitTier.ELITE: "50% increased range\n50% increased projectile speed"
    },
    UnitType.CORE_VETERAN: {
        UnitTier.ADVANCED: "25% increased health and damage",
        UnitTier.ELITE: "25% increased movement and attack speed"
    },
    UnitType.CORE_CAVALRY: {
        UnitTier.ADVANCED: "60% increased health",
        UnitTier.ELITE: "60% increased health"
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
    UnitType.ORC_BERSERKER: {
        UnitTier.ADVANCED: "50% increased damage",
        UnitTier.ELITE: "50% increased life"
    },
    UnitType.ORC_WARRIOR: {
        UnitTier.ADVANCED: "30% increased health and damage",
        UnitTier.ELITE: "30% increased movement and attack speed"
    },
    UnitType.ORC_WARCHIEF: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.ORC_GOBLIN: {
        UnitTier.ADVANCED: "goes invisible at the start of combat",
        UnitTier.ELITE: "25% increased movement and attack speed"
    },
    UnitType.ORC_WARG_RIDER: {
        UnitTier.ADVANCED: "25% increased attack and movement speed",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.CORE_WIZARD: {
        UnitTier.ADVANCED: "50% increased damage",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.INFANTRY_BANNER_BEARER: {
        UnitTier.ADVANCED: "50% increased health\nAura grants 25% increased damage",
        UnitTier.ELITE: "50% increased health\nAura grants 25% increased attack speed"
    },
    UnitType.CRUSADER_BLACK_KNIGHT: {
        UnitTier.ADVANCED: "30% increased health and movement speed",
        UnitTier.ELITE: "60% increased damage"
    },
    UnitType.INFANTRY_CATAPULT: {
        UnitTier.ADVANCED: "25% increased health and damage",
        UnitTier.ELITE: "25% reduced minimum range"
    },
    UnitType.CRUSADER_CLERIC: {
        UnitTier.ADVANCED: "100% increased range",
        UnitTier.ELITE: "50% increased attack speed"
    },
    UnitType.MISC_COMMANDER: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.INFANTRY_CROSSBOWMAN: {
        UnitTier.ADVANCED: "Gains Heavily Armored",
        UnitTier.ELITE: "25% increased damage and attack speed"
    },
    UnitType.CORE_DEFENDER: {
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
    UnitType.INFANTRY_PIKEMAN: {
        UnitTier.ADVANCED: "30% increased damage\n15% increased health",
        UnitTier.ELITE: "30% increased damage\n15% increased health"
    },
    UnitType.MISC_RED_KNIGHT: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.INFANTRY_SOLDIER: {
        UnitTier.ADVANCED: "20% increased health, damage, and range",
        UnitTier.ELITE: "20% increased health, damage, and range"
    },
    UnitType.ZOMBIE_BASIC_ZOMBIE: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.MISC_BRUTE: {
        UnitTier.ADVANCED: "25% increased health and damage",
        UnitTier.ELITE: "25% increased health and damage"
    },
    UnitType.ZOMBIE_FIGHTER: {
        UnitTier.ADVANCED: "30% increased health and damage",
        UnitTier.ELITE: "30% increased health and damage"
    },
    UnitType.SKELETON_ARCHER: {
        UnitTier.ADVANCED: "50% increased attack speed",
        UnitTier.ELITE: "50% increased range\n50% increased projectile speed"
    },
    UnitType.SKELETON_ARCHER_NECROMANCER: {
        UnitTier.ADVANCED: "Minions have 50% increased attack speed",
        UnitTier.ELITE: "Minions have 50% increased range\nMinions have 50% increased projectile speed"
    },
    UnitType.SKELETON_MAGE: {
        UnitTier.ADVANCED: "50% increased damage",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.SKELETON_MAGE_NECROMANCER: {
        UnitTier.ADVANCED: "Minions have 50% increased damage",
        UnitTier.ELITE: "Minions have 50% increased damage"
    },
    UnitType.SKELETON_SWORDSMAN: {
        UnitTier.ADVANCED: "30% increased health and damage",
        UnitTier.ELITE: "30% increased health and damage"
    },
    UnitType.SKELETON_SWORDSMAN_NECROMANCER: {
        UnitTier.ADVANCED: "Minions have 50% increased health and damage",
        UnitTier.ELITE: "Minions have 50% increased health and damage"
    },
    UnitType.SKELETON_LICH: {
        UnitTier.ADVANCED: "Revives units at Advanced tier",
        UnitTier.ELITE: "Revives units at Elite tier"
    },
    UnitType.SKELETON_HORSEMAN: {
        UnitTier.ADVANCED: "50% increased health",
        UnitTier.ELITE: "50% increased health"
    },
    UnitType.SKELETON_HORSEMAN_NECROMANCER: {
        UnitTier.ADVANCED: "Minions have 50% increased health",
        UnitTier.ELITE: "Minions have 50% increased health"
    },
    UnitType.MISC_GRABBER: {
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
    },
    UnitType.PIRATE_CREW: {
        UnitTier.ADVANCED: "25% increased attack and movement speed",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.PIRATE_GUNNER: {
        UnitTier.ADVANCED: "70% increased gun damage",
        UnitTier.ELITE: "70% increased gun damage"
    },
    UnitType.PIRATE_CANNON: {
        UnitTier.ADVANCED: "50% increased damage",
        UnitTier.ELITE: "50% increased damage"
    },
    UnitType.PIRATE_CAPTAIN: {
        UnitTier.ADVANCED: "100% increased cooldown recovery",
        UnitTier.ELITE: "30% increased damage and health"
    },
    UnitType.PIRATE_HARPOONER: {
        UnitTier.ADVANCED: "100% increased cooldown recovery",
        UnitTier.ELITE: "25% increased damage and health"
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
    
    if unit_type == UnitType.CORE_VETERAN:
        # Calculate tier-specific values
        veteran_health = gc.CORE_VETERAN_HP
        veteran_damage = gc.CORE_VETERAN_ATTACK_DAMAGE
        veteran_movement_speed = gc.CORE_VETERAN_MOVEMENT_SPEED
        attack_animation_duration = gc.CORE_VETERAN_ANIMATION_ATTACK_DURATION
        
        # Advanced tier (and Elite): 25% more health and damage
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            veteran_health = veteran_health * 1.25
            veteran_damage = veteran_damage * 1.25
        
        # Elite tier: additional 25% faster movement speed and attack speed
        if unit_tier == UnitTier.ELITE:
            veteran_movement_speed = veteran_movement_speed * 1.25
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return UnitData(
            name="Veteran",
            description=f"Veterans are durable melee units that deal damage in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(veteran_health),
                StatType.SPEED: speed_stat(veteran_movement_speed),
                StatType.DAMAGE: damage_stat(veteran_damage / attack_animation_duration, 1.5),
                StatType.RANGE: range_stat(gc.CORE_VETERAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{veteran_health:.0f} maximum health",
                StatType.SPEED: f"{veteran_movement_speed:.0f} units per second",
                StatType.DAMAGE: f"{veteran_damage:.0f} per hit ({veteran_damage / attack_animation_duration:.1f} per second) in a medium area",
                StatType.RANGE: f"{gc.CORE_VETERAN_ATTACK_RANGE} units",
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
    
    if unit_type == UnitType.SKELETON_HORSEMAN:
        # Calculate tier-specific values
        skeleton_horseman_health = gc.SKELETON_HORSEMAN_HP
        skeleton_horseman_damage = gc.SKELETON_HORSEMAN_ATTACK_DAMAGE
        
        # Advanced tier: 60% more health (cavalry-style upgrades)
        if unit_tier == UnitTier.ADVANCED:
            skeleton_horseman_health = skeleton_horseman_health * 1.6
        
        # Elite tier: another +60% HP (total 2.2x base health)
        elif unit_tier == UnitTier.ELITE:
            skeleton_horseman_health = skeleton_horseman_health * 2.2
        
        return UnitData(
            name="Skeleton Horseman",
            description="Fast undead melee units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that deal low damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(skeleton_horseman_health),
                StatType.SPEED: speed_stat(gc.SKELETON_HORSEMAN_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(skeleton_horseman_damage / gc.SKELETON_HORSEMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.SKELETON_HORSEMAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{skeleton_horseman_health:.0f} maximum health",
                StatType.SPEED: f"{gc.SKELETON_HORSEMAN_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{skeleton_horseman_damage:.0f} per hit ({skeleton_horseman_damage / gc.SKELETON_HORSEMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.SKELETON_HORSEMAN_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against ranged units", "With other fast units", "Tanking damage"],
                "Weak when": ["Against stronger melee units", "Against area of effect"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0
            }
        )

    if unit_type in (
        UnitType.SKELETON_ARCHER_NECROMANCER,
        UnitType.SKELETON_HORSEMAN_NECROMANCER,
        UnitType.SKELETON_MAGE_NECROMANCER,
        UnitType.SKELETON_SWORDSMAN_NECROMANCER,
    ):
        if unit_type == UnitType.SKELETON_ARCHER_NECROMANCER:
            minion_type = UnitType.SKELETON_ARCHER
            name = "Skeleton Archer Necromancer"
            minion_name = "Skeleton Archers"
            cooldown = gc.SKELETON_ARCHER_NECROMANCER_COOLDOWN
        elif unit_type == UnitType.SKELETON_HORSEMAN_NECROMANCER:
            minion_type = UnitType.SKELETON_HORSEMAN
            name = "Skeleton Horseman Necromancer"
            minion_name = "Skeleton Horsemen"
            cooldown = gc.SKELETON_HORSEMAN_NECROMANCER_COOLDOWN
        elif unit_type == UnitType.SKELETON_MAGE_NECROMANCER:
            minion_type = UnitType.SKELETON_MAGE
            name = "Skeleton Mage Necromancer"
            minion_name = "Skeleton Mages"
            cooldown = gc.SKELETON_MAGE_NECROMANCER_COOLDOWN
        else:
            minion_type = UnitType.SKELETON_SWORDSMAN
            name = "Skeleton Swordsman Necromancer"
            minion_name = "Skeleton Swordsmen"
            cooldown = gc.SKELETON_SWORDSMAN_NECROMANCER_COOLDOWN

        return UnitData(
            name=name,
            description=(
                f"<a href='{GlossaryEntryType.FOLLOWER.value}'>Follower</a> that summons "
                f"<a href='{minion_type.value}'>{minion_name}</a> continuously."
            ),
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.SKELETON_NECROMANCER_HP),
                StatType.SPEED: speed_stat(gc.SKELETON_NECROMANCER_MOVEMENT_SPEED),
                StatType.DAMAGE: None,
                StatType.RANGE: range_stat(gc.SKELETON_NECROMANCER_ATTACK_RANGE),
                StatType.UTILITY: 12 if unit_tier == UnitTier.ADVANCED else 16 if unit_tier == UnitTier.ELITE else 8,
            },
            tooltips={
                StatType.DEFENSE: f"{gc.SKELETON_NECROMANCER_HP} maximum health",
                StatType.SPEED: f"{gc.SKELETON_NECROMANCER_MOVEMENT_SPEED} units per second",
                StatType.RANGE: f"{gc.SKELETON_NECROMANCER_ATTACK_RANGE} units",
                StatType.DAMAGE: None,
                StatType.UTILITY: f"Summons every {cooldown:.1f}s",
            },
            tips={
                "Strong when": ["Allies protect them", "Summons can distract", "Long battles"],
                "Weak when": ["Targetted directly", "Against area of effect units"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.DAMAGE: 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 1,
            },
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
    
    if unit_type == UnitType.SKELETON_ARCHER:
        # Calculate tier-specific values
        skeleton_archer_damage = gc.SKELETON_ARCHER_ATTACK_DAMAGE
        attack_range = gc.SKELETON_ARCHER_ATTACK_RANGE
        attack_animation_duration = gc.SKELETON_ARCHER_ANIMATION_ATTACK_DURATION
        projectile_speed = gc.SKELETON_ARCHER_PROJECTILE_SPEED
        
        # Advanced tier: 50% faster rate of fire
        if unit_tier == UnitTier.ADVANCED:
            attack_animation_duration = attack_animation_duration * 2/3  # 50% faster = 2/3 duration
        
        # Elite tier: 50% more range and projectile speed
        if unit_tier == UnitTier.ELITE:
            attack_range = attack_range * 1.5
            projectile_speed = projectile_speed * 1.5
        
        return UnitData(
            name="Skeleton Archer",
            description="Skeleton Archers are ranged units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that deal low damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.SKELETON_ARCHER_HP),
                StatType.SPEED: speed_stat(gc.SKELETON_ARCHER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(skeleton_archer_damage / attack_animation_duration),
                StatType.RANGE: range_stat(attack_range),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.SKELETON_ARCHER_HP} maximum health",
                StatType.SPEED: f"{gc.SKELETON_ARCHER_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: f"{skeleton_archer_damage:.0f} per hit ({skeleton_archer_damage / attack_animation_duration:.1f} per second)" + (f". Projectile speed: {projectile_speed:.0f}" if unit_tier == UnitTier.ELITE else ""),
                StatType.RANGE: f"{attack_range:.0f} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["At long range", "Against slow units", "In a large group"],
                "Weak when": ["In close combat", "Against fast units", "Against armored units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
                )
    
    if unit_type == UnitType.SKELETON_MAGE:
        # Calculate tier-specific damage
        skeleton_mage_damage = gc.SKELETON_MAGE_ATTACK_DAMAGE
        
        # Advanced tier: 50% more damage
        if unit_tier == UnitTier.ADVANCED:
            skeleton_mage_damage = skeleton_mage_damage * 1.5
        
        # Elite tier: 100% more damage total
        elif unit_tier == UnitTier.ELITE:
            skeleton_mage_damage = skeleton_mage_damage * 2.0
        
        return UnitData(
            name="Skeleton Mage",
            description="Skeleton Mages are ranged units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that deal area damage with exploding projectiles.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.SKELETON_MAGE_HP),
                StatType.SPEED: speed_stat(gc.SKELETON_MAGE_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(skeleton_mage_damage / gc.SKELETON_MAGE_ANIMATION_ATTACK_DURATION, 2),
                StatType.RANGE: range_stat(gc.SKELETON_MAGE_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.SKELETON_MAGE_HP} maximum health",
                StatType.SPEED: f"{gc.SKELETON_MAGE_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{int(skeleton_mage_damage)} per hit ({skeleton_mage_damage / gc.SKELETON_MAGE_ANIMATION_ATTACK_DURATION:.1f} per second) in a small area",
                StatType.RANGE: f"{gc.SKELETON_MAGE_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against tightly packed groups", "Against slow units"],
                "Weak when": ["Against fast melee units", "Allies are in the way", "Against fast units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.SKELETON_SWORDSMAN:
        # Calculate tier-specific values
        skeleton_swordsman_damage = gc.SKELETON_SWORDSMAN_ATTACK_DAMAGE
        skeleton_swordsman_health = gc.SKELETON_SWORDSMAN_HP
        
        # Advanced tier: 30% more health and damage
        if unit_tier == UnitTier.ADVANCED:
            skeleton_swordsman_damage = skeleton_swordsman_damage * 1.3
            skeleton_swordsman_health = skeleton_swordsman_health * 1.3
        
        # Elite tier: 60% more health and damage (total)
        elif unit_tier == UnitTier.ELITE:
            skeleton_swordsman_damage = skeleton_swordsman_damage * 1.6
            skeleton_swordsman_health = skeleton_swordsman_health * 1.6
        
        return UnitData(
            name="Skeleton Swordsman",
            description="Skeleton Swordsmen are melee units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that deal moderate damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(skeleton_swordsman_health),
                StatType.SPEED: speed_stat(gc.SKELETON_SWORDSMAN_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(skeleton_swordsman_damage / gc.SKELETON_SWORDSMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.SKELETON_SWORDSMAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(skeleton_swordsman_health)} maximum health",
                StatType.SPEED: f"{gc.SKELETON_SWORDSMAN_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{int(skeleton_swordsman_damage)} per hit ({skeleton_swordsman_damage / gc.SKELETON_SWORDSMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.SKELETON_SWORDSMAN_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["In a large group", "In close combat"],
                "Weak when": ["Against ranged units", "<a href='Against {GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )

    if unit_type == UnitType.ORC_BERSERKER:
        # Calculate tier-specific values
        orc_berserker_ranged_damage = gc.ORC_BERSERKER_RANGED_DAMAGE
        orc_berserker_melee_damage = gc.ORC_BERSERKER_MELEE_DAMAGE
        orc_berserker_health = gc.ORC_BERSERKER_HP
        orc_berserker_movement_speed = gc.ORC_BERSERKER_MOVEMENT_SPEED
        orc_berserker_throwing_animation_duration = gc.ORC_BERSERKER_ANIMATION_THROWING_DURATION
        orc_berserker_melee_animation_duration = gc.ORC_BERSERKER_ANIMATION_MELEE_DURATION
        
        # Advanced tier: 50% increased damage
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            orc_berserker_ranged_damage = orc_berserker_ranged_damage * 1.5
            orc_berserker_melee_damage = orc_berserker_melee_damage * 1.5
        
        # Elite tier: 50% increased life
        if unit_tier == UnitTier.ELITE:
            orc_berserker_health = orc_berserker_health * 1.5
        
        return UnitData(
            name="Orc Berserker",
            description="Orc Berserkers can throwing axes at short range and use melee attacks. They start at half health and heal for half of their maximum health from <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blows</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(orc_berserker_health),
                StatType.SPEED: speed_stat(orc_berserker_movement_speed),
                StatType.DAMAGE: damage_stat(orc_berserker_melee_damage * 2 / orc_berserker_melee_animation_duration),
                StatType.RANGE: range_stat(gc.ORC_BERSERKER_RANGED_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(orc_berserker_health)} maximum health. Starts at half health. Recovers half of maximum health over 1 second from Killing Blows.",
                StatType.SPEED: f"{orc_berserker_movement_speed:.1f} units per second",
                StatType.DAMAGE: f"Ranged: {int(orc_berserker_ranged_damage)} per hit ({orc_berserker_ranged_damage / orc_berserker_throwing_animation_duration:.1f} per second), Melee: {int(orc_berserker_melee_damage)}x2 per hit ({orc_berserker_melee_damage * 2 / orc_berserker_melee_animation_duration:.1f} per second)",
                StatType.RANGE: f"Melee: {gc.ORC_BERSERKER_MELEE_RANGE} units, Ranged: {gc.ORC_BERSERKER_RANGED_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to damage slow melee units with ranged attacks", "Able to adapt to different ranges", "Able to kill multiple units quickly", "Paired with healing units"],
                "Weak when": ["Overwhelmed before killing any units", "Against high armor units", "Against powerful melee units", "Against very long ranged units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.ORC_WARRIOR:
        # Calculate tier-specific values
        orc_warrior_damage = gc.ORC_WARRIOR_ATTACK_DAMAGE
        orc_warrior_health = gc.ORC_WARRIOR_HP
        orc_warrior_movement_speed = gc.ORC_WARRIOR_MOVEMENT_SPEED
        orc_warrior_attack_animation_duration = gc.ORC_WARRIOR_ANIMATION_ATTACK_DURATION
        
        # Advanced tier: 30% more health and damage
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            orc_warrior_damage = orc_warrior_damage * 1.3
            orc_warrior_health = orc_warrior_health * 1.3
        
        # Elite tier: 30% increased movement and attack speed
        if unit_tier == UnitTier.ELITE:
            orc_warrior_movement_speed = gc.ORC_WARRIOR_MOVEMENT_SPEED * 1.3
            orc_warrior_attack_animation_duration = gc.ORC_WARRIOR_ANIMATION_ATTACK_DURATION * 0.77  # 30% faster = 0.77x duration
        
        return UnitData(
            name="Orc Warrior",
            description="Orc Warriors are balanced melee units that deal high damage. They start at half health and heal for half of their maximum health from Killing Blows.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(orc_warrior_health),
                StatType.SPEED: speed_stat(orc_warrior_movement_speed),
                StatType.DAMAGE: damage_stat(orc_warrior_damage / orc_warrior_attack_animation_duration),
                StatType.RANGE: range_stat(gc.ORC_WARRIOR_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(orc_warrior_health)} maximum health. Starts at half health. Recovers half of maximum health over 1 second from Killing Blows.",
                StatType.SPEED: f"{orc_warrior_movement_speed:.1f} units per second",
                StatType.DAMAGE: f"{int(orc_warrior_damage)} per hit ({orc_warrior_damage / orc_warrior_attack_animation_duration:.1f} per second)",
                StatType.RANGE: f"{gc.ORC_WARRIOR_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against weaker melee units", "In a large group", "Able to kill multiple units quickly", "Paired with healing units"],
                "Weak when": ["Against ranged units", "Overwhelmed before killing any units", "Against powerful melee units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 0
            }
        )
    
    if unit_type == UnitType.ORC_WARCHIEF:
        # Calculate tier-specific values
        orc_warchief_damage = gc.ORC_WARCHIEF_ATTACK_DAMAGE
        orc_warchief_health = gc.ORC_WARCHIEF_HP
        
        # Advanced tier: 50% increased health
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            orc_warchief_health = orc_warchief_health * 1.5
        
        # Elite tier: 50% increased damage
        if unit_tier == UnitTier.ELITE:
            orc_warchief_damage = orc_warchief_damage * 1.5
        
        return UnitData(
            name="Orc Warchief",
            description="Orc Warchiefs are powerful melee units with high health and damage. They start at half health and heal for half of their maximum health from <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blows</a>, while also gaining additional maximum health equal to the target's maximum health.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(orc_warchief_health + 2000),
                StatType.SPEED: speed_stat(gc.ORC_WARCHIEF_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(orc_warchief_damage / gc.ORC_WARCHIEF_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ORC_WARCHIEF_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(orc_warchief_health)} maximum health. Starts at half health. Recovers half of maximum health over 1 second and gains additional maximum health equal to the target's maximum health from Killing Blows.",
                StatType.SPEED: f"{gc.ORC_WARCHIEF_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{int(orc_warchief_damage)} per hit ({orc_warchief_damage / gc.ORC_WARCHIEF_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.ORC_WARCHIEF_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to gain a large amount of health from killing units", "Able to kill multiple units quickly", "Able to kill units with high health", "Paired with healing units"],
                "Weak when": ["Against ranged units", "Overwhelmed before killing any units", "Against even more powerful melee units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
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
    
    if unit_type == UnitType.INFANTRY_BANNER_BEARER:
        infantry_banner_bearer_health = gc.INFANTRY_BANNER_BEARER_HP
        if unit_tier == UnitTier.ADVANCED:
            infantry_banner_bearer_health = gc.INFANTRY_BANNER_BEARER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            infantry_banner_bearer_health = gc.INFANTRY_BANNER_BEARER_HP * 2.0
        
        # Generate tier-specific utility tooltip
        utility_description = f"Aura sets ally movement speed to {gc.INFANTRY_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second"
        
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            utility_description += f" and grants +{int(gc.INFANTRY_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE * 100)}% damage"
        
        if unit_tier == UnitTier.ELITE:
            utility_description += " and +25% attack speed"
        
        utility_description += f" in a radius of {gc.INFANTRY_BANNER_BEARER_AURA_RADIUS}"
        
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
                StatType.DEFENSE: defense_stat(infantry_banner_bearer_health),
                StatType.SPEED: speed_stat(gc.INFANTRY_BANNER_BEARER_AURA_MOVEMENT_SPEED),
                StatType.UTILITY: 6 if unit_tier == UnitTier.BASIC else 12 if unit_tier == UnitTier.ADVANCED else 18,
                StatType.DAMAGE: None,
                StatType.RANGE: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(infantry_banner_bearer_health)} maximum health",
                StatType.SPEED: f"{gc.INFANTRY_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second",
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
    
    if unit_type == UnitType.INFANTRY_CATAPULT:
        # Calculate tier-specific values
        catapult_health = gc.INFANTRY_CATAPULT_HP
        catapult_damage = gc.INFANTRY_CATAPULT_DAMAGE
        catapult_min_range = gc.INFANTRY_CATAPULT_MINIMUM_RANGE
        catapult_max_range = gc.INFANTRY_CATAPULT_MAXIMUM_RANGE
        
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
                StatType.DAMAGE: damage_stat(catapult_damage / gc.INFANTRY_CATAPULT_COOLDOWN, 3),
                StatType.RANGE: range_stat(catapult_max_range),
                StatType.SPEED: None,
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(catapult_health)} maximum health",
                StatType.DAMAGE: f"{int(catapult_damage)} per hit ({catapult_damage / gc.INFANTRY_CATAPULT_COOLDOWN:.1f} per second) in a medium area",
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
    
    if unit_type == UnitType.MISC_COMMANDER:
        commander_health = gc.MISC_COMMANDER_HP
        if unit_tier == UnitTier.ADVANCED:
            commander_health = gc.MISC_COMMANDER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            commander_health = gc.MISC_COMMANDER_HP * 2.0
        
        return UnitData(
            name="Commander",
            description=f"Commanders are support units with an <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(commander_health),
                StatType.SPEED: speed_stat(gc.MISC_COMMANDER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.MISC_COMMANDER_ATTACK_DAMAGE / gc.MISC_COMMANDER_ANIMATION_ATTACK_DURATION),
                StatType.UTILITY: 6,
                StatType.RANGE: range_stat(gc.MISC_COMMANDER_ATTACK_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{commander_health} maximum health",
                StatType.SPEED: f"{gc.MISC_COMMANDER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.MISC_COMMANDER_ATTACK_DAMAGE} per hit ({gc.MISC_COMMANDER_ATTACK_DAMAGE / gc.MISC_COMMANDER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.UTILITY: f"Aura grants +{int(gc.MISC_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE * 100)}% damage to allies in a radius of {gc.MISC_COMMANDER_AURA_RADIUS}",
                StatType.RANGE: f"{gc.MISC_COMMANDER_ATTACK_RANGE} units"
            },
            tips={
                "Strong when": ["In a large group", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
                "Weak when": [f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>", "When allies are too far away"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.INFANTRY_CROSSBOWMAN:
        # Calculate tier-specific values
        crossbowman_health = gc.INFANTRY_CROSSBOWMAN_HP
        crossbowman_damage = gc.INFANTRY_CROSSBOWMAN_ATTACK_DAMAGE
        crossbowman_attack_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_ATTACK_DURATION
        crossbowman_reload_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_RELOAD_DURATION
        crossbowman_armored = True
        crossbowman_heavily_armored = False
        description = f"Crossbowmen are medium-ranged <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can fire multiple shots before needing to reload."
        defense_tooltip = f"{crossbowman_health} maximum health, armored"
        
        # Advanced tier (and Elite): Gains heavy armor
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            crossbowman_heavily_armored = True
            crossbowman_armored = False
            description = f"Crossbowmen are medium-ranged <a href='{GlossaryEntryType.HEAVILY_ARMORED.value}'>Heavily Armored</a> units that can fire multiple shots before needing to reload."
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
                StatType.RANGE: range_stat(gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.INFANTRY_CROSSBOWMAN_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: defense_tooltip,
                StatType.DAMAGE: f"{crossbowman_damage} per hit ({crossbowman_damage / crossbowman_attack_duration:.1f} per second while attacking, {crossbowman_damage / (crossbowman_attack_duration + crossbowman_reload_duration/2):.1f} per second including reloading). Starts with {gc.INFANTRY_CROSSBOWMAN_STARTING_AMMO} ammo, and can reload to regain ammo, up to {gc.INFANTRY_CROSSBOWMAN_MAX_AMMO}.",
                StatType.RANGE: f"{gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.INFANTRY_CROSSBOWMAN_MOVEMENT_SPEED} units per second",
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
    
    if unit_type == UnitType.CORE_DEFENDER:
        # Calculate tier-specific values
        defender_health = gc.CORE_DEFENDER_HP
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
                StatType.DAMAGE: damage_stat(gc.CORE_DEFENDER_ATTACK_DAMAGE / gc.CORE_DEFENDER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_DEFENDER_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CORE_DEFENDER_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: defense_tooltip,
                StatType.DAMAGE: f"{gc.CORE_DEFENDER_ATTACK_DAMAGE} per hit ({gc.CORE_DEFENDER_ATTACK_DAMAGE / gc.CORE_DEFENDER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_DEFENDER_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CORE_DEFENDER_MOVEMENT_SPEED} units per second",
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
    
    if unit_type == UnitType.INFANTRY_PIKEMAN:
        # Calculate tier-specific values
        pikeman_health = gc.INFANTRY_PIKEMAN_HP
        pikeman_damage = gc.INFANTRY_PIKEMAN_ATTACK_DAMAGE
        
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
                StatType.DAMAGE: damage_stat(pikeman_damage / gc.INFANTRY_PIKEMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.INFANTRY_PIKEMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.INFANTRY_PIKEMAN_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{pikeman_health:.0f} maximum health",
                StatType.DAMAGE: f"{pikeman_damage:.0f} per hit ({pikeman_damage / gc.INFANTRY_PIKEMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.INFANTRY_PIKEMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.INFANTRY_PIKEMAN_MOVEMENT_SPEED} units per second",
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
    
    if unit_type == UnitType.MISC_RED_KNIGHT:
        red_knight_health = gc.MISC_RED_KNIGHT_HP
        if unit_tier == UnitTier.ADVANCED:
            red_knight_health = gc.MISC_RED_KNIGHT_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            red_knight_health = gc.MISC_RED_KNIGHT_HP * 2.0
        
        return UnitData(
            name="Red Knight",
            description=f"Red Knights are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can switch between melee and ranged attacks.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(red_knight_health, armored=True),
                StatType.DAMAGE: damage_stat(gc.MISC_RED_KNIGHT_ATTACK_DAMAGE / gc.MISC_RED_KNIGHT_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.MISC_RED_KNIGHT_ATTACK_RANGE),    
                StatType.SPEED: speed_stat(gc.MISC_RED_KNIGHT_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{red_knight_health} maximum health, armored",
                StatType.DAMAGE: f"{gc.MISC_RED_KNIGHT_ATTACK_DAMAGE} per hit ({gc.MISC_RED_KNIGHT_ATTACK_DAMAGE / gc.MISC_RED_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.MISC_RED_KNIGHT_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.MISC_RED_KNIGHT_MOVEMENT_SPEED} units per second",
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
    
    if unit_type == UnitType.INFANTRY_SOLDIER:
        # Calculate tier-specific values
        soldier_health = gc.INFANTRY_SOLDIER_HP
        soldier_melee_damage = gc.INFANTRY_SOLDIER_MELEE_DAMAGE
        soldier_ranged_damage = gc.CORE_ARCHER_ATTACK_DAMAGE
        soldier_ranged_range = gc.INFANTRY_SOLDIER_RANGED_RANGE
        
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
                StatType.DAMAGE: damage_stat(soldier_melee_damage / gc.INFANTRY_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION),
                StatType.RANGE: range_stat(soldier_ranged_range),
                StatType.SPEED: speed_stat(gc.INFANTRY_SOLDIER_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{soldier_health:.0f} maximum health, armored",
                StatType.DAMAGE: f"Melee: {soldier_melee_damage:.0f} per hit ({soldier_melee_damage / gc.INFANTRY_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION:.1f} per second), Ranged: {soldier_ranged_damage:.0f} per hit ({soldier_ranged_damage / gc.INFANTRY_SOLDIER_ANIMATION_RANGED_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"Melee: {gc.INFANTRY_SOLDIER_MELEE_RANGE} units, Ranged: {soldier_ranged_range:.0f} units",
                StatType.SPEED: f"{gc.INFANTRY_SOLDIER_MOVEMENT_SPEED} units per second",
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
    if unit_type == UnitType.ZOMBIE_FIGHTER:
        # Calculate tier-specific values
        zombie_fighter_health = gc.ZOMBIE_FIGHTER_HP
        zombie_fighter_damage = gc.ZOMBIE_FIGHTER_ATTACK_DAMAGE
        
        # Advanced tier: 30% increased health and damage
        if unit_tier == UnitTier.ADVANCED:
            zombie_fighter_health = zombie_fighter_health * 1.3
            zombie_fighter_damage = zombie_fighter_damage * 1.3
        
        # Elite tier: 60% increased health and damage total
        elif unit_tier == UnitTier.ELITE:
            zombie_fighter_health = zombie_fighter_health * 1.6
            zombie_fighter_damage = zombie_fighter_damage * 1.6
        
        return UnitData(
            name="Zombie Fighter",
            description=f"Zombie Fighters are slow melee units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> and powerful attacks that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_fighter_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_FIGHTER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(zombie_fighter_damage / gc.ZOMBIE_FIGHTER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_FIGHTER_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_fighter_health:.0f} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_FIGHTER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{zombie_fighter_damage:.0f} per hit ({zombie_fighter_damage / gc.ZOMBIE_FIGHTER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.ZOMBIE_FIGHTER_ATTACK_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["Against enemies that can be killed in one hit", "In a large group", "Tanking damage"],
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
    if unit_type == UnitType.MISC_BRUTE:
        # Calculate tier-specific values
        misc_brute_health = gc.MISC_BRUTE_HP
        misc_brute_damage = gc.MISC_BRUTE_ATTACK_DAMAGE
        
        # Advanced tier: 25% increased health and damage
        if unit_tier == UnitTier.ADVANCED:
            misc_brute_health = misc_brute_health * 1.25
            misc_brute_damage = misc_brute_damage * 1.25
        
        # Elite tier: 50% increased health and damage total
        elif unit_tier == UnitTier.ELITE:
            misc_brute_health = misc_brute_health * 1.5
            misc_brute_damage = misc_brute_damage * 1.5
        
        return UnitData(
            name="Brute",
            description=f"Brutes are slow melee units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and carry two <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> into battle.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(misc_brute_health),
                StatType.SPEED: speed_stat(gc.MISC_BRUTE_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(misc_brute_damage / gc.MISC_BRUTE_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.MISC_BRUTE_ATTACK_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{misc_brute_health:.0f} maximum health",
                StatType.SPEED: f"{gc.MISC_BRUTE_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{misc_brute_damage:.0f} per hit ({misc_brute_damage / gc.MISC_BRUTE_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.MISC_BRUTE_ATTACK_RANGE} units",
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
    
    if unit_type == UnitType.MISC_GRABBER:
        # Calculate tier-specific values
        misc_grabber_health = gc.MISC_GRABBER_HP
        grab_damage = gc.MISC_GRABBER_GRAB_DAMAGE
        melee_damage = gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE
        
        # Advanced tier: 50% increased health and damage
        if unit_tier == UnitTier.ADVANCED:
            misc_grabber_health = misc_grabber_health * 1.5
            grab_damage = grab_damage * 1.5
            melee_damage = melee_damage * 1.5
        
        # Elite tier: 100% increased health and damage total
        elif unit_tier == UnitTier.ELITE:
            misc_grabber_health = misc_grabber_health * 2.0
            grab_damage = grab_damage * 2.0
            melee_damage = melee_damage * 2.0
        
        return UnitData(
            name="Grabber",
            description=f"Grabbers are slow melee units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> and long reach that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and can grab and pull enemies towards them.",
            tier=unit_tier,
            stats={ 
                StatType.DEFENSE: defense_stat(misc_grabber_health),
                StatType.SPEED: speed_stat(gc.MISC_GRABBER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(melee_damage / gc.MISC_GRABBER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.MISC_GRABBER_GRAB_MAXIMUM_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{misc_grabber_health:.0f} maximum health",
                StatType.SPEED: f"{gc.MISC_GRABBER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{melee_damage:.0f} per hit ({melee_damage / gc.MISC_GRABBER_ANIMATION_ATTACK_DURATION:.1f} per second), Grab deals {grab_damage:.0f} per hit with a {gc.MISC_GRABBER_GRAB_COOLDOWN} second cooldown",
                StatType.RANGE: f"Melee: {gc.MISC_GRABBER_ATTACK_RANGE} units, Grab: {gc.MISC_GRABBER_GRAB_MINIMUM_RANGE} to {gc.MISC_GRABBER_GRAB_MAXIMUM_RANGE} units",
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
    
    if unit_type == UnitType.PIRATE_HARPOONER:
        # Calculate tier-specific values
        harpooner_health = gc.PIRATE_HARPOONER_HP
        harpoon_damage = gc.PIRATE_HARPOONER_HARPOON_DAMAGE
        melee_damage = gc.PIRATE_HARPOONER_ATTACK_DAMAGE
        harpoon_cooldown = gc.PIRATE_HARPOONER_HARPOON_COOLDOWN
        
        # Advanced tier: 50% cooldown recovery (faster cooldown)
        if unit_tier == UnitTier.ADVANCED:
            harpoon_cooldown = harpoon_cooldown * 0.5
        
        # Elite tier: 25% increased attack damage and health
        elif unit_tier == UnitTier.ELITE:
            harpooner_health = harpooner_health * 1.25
            harpoon_damage = harpoon_damage * 1.25
            melee_damage = melee_damage * 1.25
            harpoon_cooldown = harpoon_cooldown * 0.5  # Keep the cooldown improvement from advanced
        
        return UnitData(
            name="Harpooner",
            description="Harpooners are melee units that cangrab and pull enemies towards them with their harpoons.",
            tier=unit_tier,
            stats={ 
                StatType.DEFENSE: defense_stat(harpooner_health),
                StatType.SPEED: speed_stat(gc.PIRATE_HARPOONER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(melee_damage / gc.PIRATE_HARPOONER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.PIRATE_HARPOONER_HARPOON_MAXIMUM_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{harpooner_health:.0f} maximum health",
                StatType.SPEED: f"{gc.PIRATE_HARPOONER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{melee_damage:.0f} per hit ({melee_damage / gc.PIRATE_HARPOONER_ANIMATION_ATTACK_DURATION:.1f} per second), Harpoon deals {harpoon_damage:.0f} per hit with a {harpoon_cooldown:.1f} second cooldown",
                StatType.RANGE: f"Melee: {gc.PIRATE_HARPOONER_ATTACK_RANGE} units, Harpoon: {gc.PIRATE_HARPOONER_HARPOON_MINIMUM_RANGE} to {gc.PIRATE_HARPOONER_HARPOON_MAXIMUM_RANGE} units",
                StatType.UTILITY: f"Can grab and pull enemies towards them with harpoons"
            },
            tips={
                "Strong when": ["Pulling enemy units into a group of allies", "In a large group", "Behind other units", "Against ranged units"],
                "Weak when": ["In one-on-one combat", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0 if unit_tier == UnitTier.BASIC else 1
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
            description=f"Jumpers are fast, high damage <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and can jump to their target.",
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
        spitter_damage = gc.ZOMBIE_SPITTER_RANGED_ATTACK_DAMAGE
        melee_damage = gc.ZOMBIE_SPITTER_MELEE_ATTACK_DAMAGE
        
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
            description=f"Spitters are slow, short-ranged <a href='{GlossaryEntryType.SPREADER.value}'>Spreaders</a> with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> that <a href='{GlossaryEntryType.POISON.value}'>Poison</a> and <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.ZOMBIE_SPITTER_HP),
                StatType.SPEED: speed_stat(gc.ZOMBIE_SPITTER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(spitter_damage / gc.ZOMBIE_SPITTER_ANIMATION_RANGED_ATTACK_DURATION, 2/3),
                StatType.RANGE: range_stat(gc.ZOMBIE_SPITTER_RANGED_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            },
            tooltips={
                StatType.DEFENSE: f"{gc.ZOMBIE_SPITTER_HP:.0f} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_SPITTER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{spitter_damage:.0f} poison damage ({spitter_damage/gc.ZOMBIE_INFECTION_DURATION:.1f} damage per second per poison) ({spitter_damage / gc.ZOMBIE_SPITTER_ANIMATION_RANGED_ATTACK_DURATION:.1f} per second if poisoning multiple enemies). Melee: {melee_damage/2:.0f} per hit (hits twice)",
                StatType.RANGE: f"{gc.ZOMBIE_SPITTER_RANGED_ATTACK_RANGE} units",
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
            description=f"Tanks are slow melee units with <a href='{GlossaryEntryType.UNUSABLE_CORPSE.value}'>Unusable Corpses</a> and very high health that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
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
    
    if unit_type == UnitType.ORC_GOBLIN:
        # Calculate tier-specific values
        orc_goblin_movement_speed = gc.ORC_GOBLIN_MOVEMENT_SPEED
        orc_goblin_attack_duration = gc.ORC_GOBLIN_ANIMATION_ATTACK_DURATION
        orc_goblin_invisible_duration = gc.ORC_GOBLIN_INVISIBLE_DURATION
        
        # Elite tier: 25% increased movement speed and ability speed
        if unit_tier == UnitTier.ELITE:
            orc_goblin_movement_speed = orc_goblin_movement_speed * 1.25
            orc_goblin_attack_duration = orc_goblin_attack_duration * 0.8  # 25% faster = 0.8x duration

        # Create description based on tier
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            description = f"Orc Goblins are fast <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that become <a href='{GlossaryEntryType.INVISIBLE.value}'>Invisible</a> at the start of combat or after getting a <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blow</a>."
        else:
            description = f"Orc Goblins are fast <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that become <a href='{GlossaryEntryType.INVISIBLE.value}'>Invisible</a> after getting a <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blow</a>."
        
        return UnitData(
            name="Orc Goblin",
            description=description,
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.ORC_GOBLIN_HP),
                StatType.SPEED: speed_stat(orc_goblin_movement_speed),
                StatType.DAMAGE: damage_stat(gc.ORC_GOBLIN_ATTACK_DAMAGE / orc_goblin_attack_duration),
                StatType.RANGE: range_stat(gc.ORC_GOBLIN_ATTACK_RANGE),
                StatType.UTILITY: 7.5 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 3
            },
            tooltips={
                StatType.DEFENSE: f"{int(gc.ORC_GOBLIN_HP)} maximum health",
                StatType.SPEED: f"{orc_goblin_movement_speed:.1f} units per second",
                StatType.DAMAGE: f"{int(gc.ORC_GOBLIN_ATTACK_DAMAGE)} per hit ({gc.ORC_GOBLIN_ATTACK_DAMAGE / orc_goblin_attack_duration:.1f} per second)",
                StatType.RANGE: f"{gc.ORC_GOBLIN_ATTACK_RANGE} units",
                StatType.UTILITY: f"Becomes invisible for {orc_goblin_invisible_duration:.1f} seconds after killing a unit"
            },
            tips={
                "Strong when": ["Able to kill units quickly", "Against isolated targets", "Enemies are distracted"],
                "Weak when": ["Against more powerful units", "Surrounded by enemies"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 0,
                StatType.RANGE: 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.ORC_WARG_RIDER:
        # Calculate tier-specific values
        warg_rider_movement_speed = gc.ORC_WARG_RIDER_MOVEMENT_SPEED
        warg_rider_attack_damage = gc.ORC_WARG_RIDER_ATTACK_DAMAGE
        warg_rider_attack_duration = gc.ORC_WARG_RIDER_ANIMATION_ATTACK_DURATION
        
        # Advanced tier: 25% increased movement speed
        if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE:
            warg_rider_movement_speed = warg_rider_movement_speed * 1.25
        
        # Elite tier: 50% increased damage
        if unit_tier == UnitTier.ELITE:
            warg_rider_attack_damage = warg_rider_attack_damage * 1.5

        return UnitData(
            name="Orc Warg Rider",
            description=f"Orc Warg Riders are fast melee units that deal two strikes when attacking. They start at half health and heal for half of their maximum health after getting a <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blow</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.ORC_WARG_RIDER_HP * 1.5),
                StatType.SPEED: speed_stat(warg_rider_movement_speed),
                StatType.DAMAGE: damage_stat(warg_rider_attack_damage / warg_rider_attack_duration),
                StatType.RANGE: range_stat(gc.ORC_WARG_RIDER_ATTACK_RANGE),
                StatType.UTILITY: None,
            },
            tooltips={
                StatType.DEFENSE: f"{int(gc.ORC_WARG_RIDER_HP)} maximum health. Starts at half health. Recovers half of maximum health over 1 second from Killing Blows.",
                StatType.SPEED: f"{warg_rider_movement_speed:.1f} units per second",
                StatType.DAMAGE: f"{warg_rider_attack_damage*2/3} + {warg_rider_attack_damage*1/3} per attack ({warg_rider_attack_damage / warg_rider_attack_duration:.1f} per second)",
                StatType.RANGE: f"{gc.ORC_WARG_RIDER_ATTACK_RANGE} units",
                StatType.UTILITY: None,
            },
            tips={
                "Strong when": ["Able to kill units quickly", "Against isolated targets", "In a group with other fast units", "Paired with healing units"],
                "Weak when": ["Against armor", "Against more powerful units", "Surrounded by enemies"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.DEFENSE: 0,
                StatType.RANGE: 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ADVANCED or unit_tier == UnitTier.ELITE else 0,
                StatType.UTILITY: 0,
            }
        )
    if unit_type == UnitType.PIRATE_CANNON:
        # Calculate tier-specific values
        cannon_damage = gc.PIRATE_CANNON_DAMAGE
        cannon_range = gc.PIRATE_CANNON_RANGE
        
        # Advanced tier: 50% increased damage
        if unit_tier == UnitTier.ADVANCED:
            cannon_damage = cannon_damage * 1.5
        
        # Elite tier: 100% increased damage total
        elif unit_tier == UnitTier.ELITE:
            cannon_damage = cannon_damage * 2.0
        
        return UnitData(
            name="Pirate Cannon",
            description="Pirate Cannons are powerful ranged units with a devastating shot that pierces through units on a long cooldown.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.PIRATE_CANNON_HP),
                StatType.SPEED: speed_stat(gc.PIRATE_CANNON_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(cannon_damage * 1.5),
                StatType.RANGE: range_stat(cannon_range),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(gc.PIRATE_CANNON_HP)} maximum health",
                StatType.SPEED: f"{gc.PIRATE_CANNON_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: f"{int(cannon_damage)} per shot that pierces through units ({gc.PIRATE_CANNON_COOLDOWN:.0f}s cooldown)",
                StatType.RANGE: f"{cannon_range} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to get a good shot", "Against high-value targets", "In a defensive position"],
                "Weak when": ["Cannon is on cooldown", "Against fast units", "Overwhelmed by enemies"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0,
            }
        )

    if unit_type == UnitType.PIRATE_CREW:
        # Calculate tier-specific values
        pirate_crew_damage = gc.PIRATE_CREW_ATTACK_DAMAGE
        pirate_crew_health = gc.PIRATE_CREW_HP
        pirate_crew_movement_speed = gc.PIRATE_CREW_MOVEMENT_SPEED
        
        # Advanced tier: 25% increased attack and movement speed
        if unit_tier == UnitTier.ADVANCED:
            pirate_crew_damage = pirate_crew_damage * 1.25
            pirate_crew_movement_speed = pirate_crew_movement_speed * 1.25
        
        # Elite tier: 50% more damage total
        elif unit_tier == UnitTier.ELITE:
            pirate_crew_damage = pirate_crew_damage * 1.5
        
        return UnitData(
            name="Pirate Crew",
            description="Pirate Crew are balanced melee units with a <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> jump attack on a long cooldown.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(pirate_crew_health),
                StatType.SPEED: speed_stat(pirate_crew_movement_speed * 1.5),
                StatType.DAMAGE: damage_stat(pirate_crew_damage / gc.PIRATE_CREW_ANIMATION_ATTACK_DURATION + 50),
                StatType.RANGE: range_stat(gc.PIRATE_CREW_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(pirate_crew_health)} maximum health",
                StatType.SPEED: f"{pirate_crew_movement_speed:.1f} units per second, can jump {gc.PIRATE_CREW_MAXIMUM_JUMP_RANGE} units every {gc.PIRATE_CREW_JUMP_COOLDOWN:.0f} seconds",
                StatType.DAMAGE: f"{int(pirate_crew_damage)} per hit ({pirate_crew_damage / gc.PIRATE_CREW_ANIMATION_ATTACK_DURATION:.1f} per second). Jump deals {gc.PIRATE_CREW_JUMP_DAMAGE} damage in a small area.",
                StatType.RANGE: f"Melee: {gc.PIRATE_CREW_ATTACK_RANGE} units, Jump: {gc.PIRATE_CREW_MINIMUM_JUMP_RANGE} to {gc.PIRATE_CREW_MAXIMUM_JUMP_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to hit multiple units with jump", "In a group with other pirate crew", "Against units with low health"],
                "Weak when": ["Against very long ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.SPEED: 1 if unit_tier == UnitTier.ADVANCED else 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0,
            }
        )
    
    if unit_type == UnitType.PIRATE_GUNNER:
        # Calculate tier-specific values
        pirate_gunner_gun_damage = gc.PIRATE_GUNNER_GUN_DAMAGE
        pirate_gunner_melee_damage = gc.PIRATE_GUNNER_MELEE_DAMAGE
        
        # Advanced tier: 70% increased gun damage
        if unit_tier == UnitTier.ADVANCED:
            pirate_gunner_gun_damage = pirate_gunner_gun_damage * 1.7
        
        # Elite tier: 140% increased gun damage total (70% + 70%)
        elif unit_tier == UnitTier.ELITE:
            pirate_gunner_gun_damage = pirate_gunner_gun_damage * 2.4
        
        return UnitData(
            name="Pirate Gunner",
            description="Pirate Gunners are ranged units with a powerful musket shot on a long cooldown and a melee attack for close combat.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.PIRATE_GUNNER_HP),
                StatType.SPEED: speed_stat(gc.PIRATE_GUNNER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(pirate_gunner_gun_damage / 1.5),
                StatType.RANGE: range_stat(gc.PIRATE_GUNNER_GUN_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(gc.PIRATE_GUNNER_HP)} maximum health",
                StatType.SPEED: f"{gc.PIRATE_GUNNER_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: f"Gun: {int(pirate_gunner_gun_damage)} ({gc.PIRATE_GUNNER_GUN_COOLDOWN:.0f}s cooldown), Melee: {int(pirate_gunner_melee_damage)} per hit ({pirate_gunner_melee_damage / gc.PIRATE_GUNNER_ANIMATION_MELEE_DURATION:.1f} per second)",
                StatType.RANGE: f"Gun: {gc.PIRATE_GUNNER_GUN_RANGE} units, Melee: {gc.PIRATE_GUNNER_MELEE_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to get a good shot with the musket", "Against high-value targets"],
                "Weak when": ["Musket is on cooldown", "Distracted by low-value targets"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0,
            }
        )
    
    if unit_type == UnitType.PIRATE_CAPTAIN:
        # Calculate tier-specific values
        pirate_captain_gun_damage = gc.PIRATE_CAPTAIN_GUN_DAMAGE
        pirate_captain_melee_damage = gc.PIRATE_CAPTAIN_MELEE_DAMAGE
        pirate_captain_health = gc.PIRATE_CAPTAIN_HP
        gun_cooldown = gc.PIRATE_CAPTAIN_GUN_COOLDOWN
        
        # Advanced tier: 50% reduced cooldown on gun attack
        if unit_tier == UnitTier.ADVANCED:
            gun_cooldown = gun_cooldown * 0.5
        
        # Elite tier: 30% increased damage and health
        if unit_tier == UnitTier.ELITE:
            pirate_captain_gun_damage = pirate_captain_gun_damage * 1.3
            pirate_captain_melee_damage = pirate_captain_melee_damage * 1.3
            pirate_captain_health = pirate_captain_health * 1.3
        
        return UnitData(
            name="Pirate Captain",
            description="Pirate Captains are powerful hybrid units with a pistol and sword.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(pirate_captain_health),
                StatType.SPEED: speed_stat(gc.PIRATE_CAPTAIN_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(pirate_captain_gun_damage / gc.PIRATE_CAPTAIN_ANIMATION_GUN_DURATION + pirate_captain_melee_damage / gc.PIRATE_CAPTAIN_ANIMATION_MELEE_DURATION),
                StatType.RANGE: range_stat(gc.PIRATE_CAPTAIN_MAXIMUM_GUN_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{int(pirate_captain_health)} maximum health",
                StatType.SPEED: f"{gc.PIRATE_CAPTAIN_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: f"Gun: {int(pirate_captain_gun_damage)} per shot ({gun_cooldown:.1f}s cooldown), Melee: {int(pirate_captain_melee_damage)} per hit ({pirate_captain_melee_damage / gc.PIRATE_CAPTAIN_ANIMATION_MELEE_DURATION:.1f} per second)",
                StatType.RANGE: f"Gun: {gc.PIRATE_CAPTAIN_MAXIMUM_GUN_RANGE} units, Melee: {gc.PIRATE_CAPTAIN_MELEE_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Able to kill low-health units from range", "Against weaker melee or ranged units", "When in a large group"],
                "Weak when": ["Against longer ranged units", "Overwhelmed by enemies"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ELITE else 0,
                StatType.SPEED: 0,
                StatType.DAMAGE: 2 if unit_tier == UnitTier.ELITE else 1 if unit_tier == UnitTier.ADVANCED else 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 0,
            }
        )
    
    if unit_type == UnitType.SKELETON_LICH:
        return UnitData(
            name="Skeleton Lich",
            description=(
                f"<a href='{GlossaryEntryType.REVIVE.value}'>Revives</a> dead units from either team at a distance. Units worth more points take longer to revive."
            ),
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.SKELETON_LICH_HP),
                StatType.SPEED: speed_stat(gc.SKELETON_LICH_MOVEMENT_SPEED),
                StatType.DAMAGE: None,
                StatType.RANGE: range_stat(gc.SKELETON_LICH_ABILITY_RANGE),
                StatType.UTILITY: 22.5 if unit_tier == UnitTier.ADVANCED else 30 if unit_tier == UnitTier.ELITE else 15,
            },
            tooltips={
                StatType.DEFENSE: f"{gc.SKELETON_LICH_HP} maximum health",
                StatType.SPEED: f"{gc.SKELETON_LICH_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: None,
                StatType.RANGE: f"{gc.SKELETON_LICH_ABILITY_RANGE:.0f} units",
                StatType.UTILITY: f"Revives units at a rate of {50/gc.SKELETON_LICH_ANIMATION_ABILITY_DURATION:.1f} points/second",
            },
            tips={
                "Strong when": ["Near many corpses", "In long battles", "Protected by allies", "Revived corpses are useful"],
                "Weak when": ["No usable corpses nearby", "Allies or enemies have Unusable Corpses", "Against fast-moving enemies", "Overwhelmed quickly"],
            },
            modification_levels={
                StatType.DEFENSE: 0,
                StatType.SPEED: 0,
                StatType.DAMAGE: 0,
                StatType.RANGE: 0,
                StatType.UTILITY: 2 if unit_tier == UnitTier.ELITE else 1 if unit_tier == UnitTier.ADVANCED else 0,
            }
        )
    
    raise ValueError(f"Unknown unit type: {unit_type}")

def get_item_data(item_type: ItemType) -> ItemData:
    """Get item data for the specified item type."""
    
    if item_type == ItemType.HEALTH_POTION:
        return ItemData(
            name="Health Potion",
            description=f"Grants the equipped unit +{gc.ITEM_HEALTH_POTION_HEALTH_BONUS} HP.",
            tips={
                "Strong when": ["Unit has low health", "Unit is a tank", "Unit needs survivability", "Long battles"],
                "Weak when": ["Unit already has high health", "Unit dies quickly anyway", "Unit is ranged and safe"],
            }
        )
    
    raise ValueError(f"Unknown item type: {item_type}")