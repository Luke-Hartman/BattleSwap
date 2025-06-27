import enum
from components.unit_tier import UnitTier
from components.unit_type import UnitType
from game_constants import gc
from typing import Dict, List, Optional
from dataclasses import dataclass

def taper(value: float) -> float:
    """Tapers the value to a stat value between 1 and 10, with a steeper curve at the end."""
    if value < 7:
        return value
    return 7 + min((value - 7)**0.5, 3)

def damage_stat(dps: float, multiplier: float = 1) -> float:
    """Maps damage to a stat value between 1 and 10."""
    stat = (dps * multiplier) / (gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE / gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION) * 5
    return taper(stat)

def defense_stat(defense: float, armored: bool = False, self_heal_dps: float = 0) -> float:
    """Maps defense to a stat value between 1 and 10."""
    stat = defense / gc.ZOMBIE_TANK_HP * 16 + self_heal_dps / (gc.CORE_SWORDSMAN_ATTACK_DAMAGE / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION) * 5
    if armored:
        stat *= 1.25
    return taper(stat)

def speed_stat(movement_speed: float) -> float:
    """Maps movement speed to a stat value between 1 and 10."""
    nine_speed = gc.CORE_CAVALRY_MOVEMENT_SPEED
    stat = (movement_speed / nine_speed) * 9
    return taper(stat)

def range_stat(range: float) -> float:
    """Maps range to a stat value between 1 and 10."""
    stat = (range / gc.CRUSADER_CATAPULT_MAXIMUM_RANGE) * 16
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
    HUNTER = "Hunter"
    POISON = "Poison"
    INFECTION = "Infection"
    KILLING_BLOW = "Killing Blow"
    POINTS = "Points"
    SPREADER = "Spreader"

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
    GlossaryEntryType.ARMORED: f"Armored units take {gc.ARMOR_FLAT_DAMAGE_REDUCTION} flat reduced damage, and have {gc.ARMOR_PERCENT_DAMAGE_REDUCTION}% damage reduction (after flat reduction). Maximum damage reduction is capped at {gc.MAX_ARMOR_DAMAGE_REDUCTION}%.",
    GlossaryEntryType.AURA: "Auras apply effects to nearby units. Some units may not be affected, such as units on the same team.",
    GlossaryEntryType.BARRACKS: "The Barracks contains your available army. It can be accessed at the bottom of the screen.",
    GlossaryEntryType.CORRUPTION: f"Corruption reopens up to {gc.CORRUPTION_BATTLE_COUNT} battles you've already completed, with modifiers to increase their difficulty. To continue, you must defeat these corrupted battles again. Corruption can activate when you exceed {gc.CORRUPTION_TRIGGER_POINTS} <a href='{GlossaryEntryType.POINTS.value}'>Points</a> in your <a href='{GlossaryEntryType.BARRACKS.value}'>Barracks</a>. Efficient players can corrupt and reconquer every battle.",
    GlossaryEntryType.FACTION: "Factions are groups of units that share a common theme. Enemy armies are made up of units from a specific faction plus the core units, while players are free to mix and match units from different factions.",
    GlossaryEntryType.FLEE: "Fleeing units move away from the source of the effect at a reduced speed for 2 seconds.",
    GlossaryEntryType.FOLLOWER: "Follower units follow a nearby friendly non-follower unit until it is killed.",
    GlossaryEntryType.HUNTER: "While most units target the nearest enemy unit, Hunters prioritize units with low current health.",
    GlossaryEntryType.POISON: "Poison damage is dealt over 2 seconds, and is not blocked by armor. Projectiles that poison pass through units that are already poisoned.",
    GlossaryEntryType.INFECTION: f"Infected units turn into <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> when they die. Infection lasts for 2 seconds.",
    GlossaryEntryType.KILLING_BLOW: "A killing blow is when an instance of damage is enough to kill a unit. Some units have special abilities that trigger when they deal a killing blow.",
    GlossaryEntryType.POINTS: f"Points represent the value of a unit. When you have more than {gc.CORRUPTION_TRIGGER_POINTS} points of units in your <a href='{GlossaryEntryType.BARRACKS.value}'>Barracks</a>, <a href='{GlossaryEntryType.CORRUPTION.value}'>Corruption</a> will trigger.",
    GlossaryEntryType.SPREADER: f"While most units target the nearest enemy unit, Spreaders prioritize units that are not <a href='{GlossaryEntryType.INFECTION.value}'>Infected</a>."
}

def get_unit_data(unit_type: UnitType, unit_tier: UnitTier = UnitTier.BASIC) -> UnitData:
    """Get unit data for the specified unit type and tier."""
    
    # Define base unit data with tier-specific calculations
    base_unit_data = {}
    
    if unit_type == UnitType.CORE_ARCHER:
        
        damage_multiplier = 1.0
        if unit_tier == UnitTier.ADVANCED:
            damage_multiplier = 1.5
        elif unit_tier == UnitTier.ELITE:
            damage_multiplier = 2.0
        
        # Calculate actual values using multipliers
        archer_damage = gc.CORE_ARCHER_ATTACK_DAMAGE * damage_multiplier
            
        return UnitData(
            name="Archer",
            description="Archers are basic ranged units that can target units from afar.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_ARCHER_HP),
                StatType.SPEED: speed_stat(gc.CORE_ARCHER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(archer_damage),
                StatType.RANGE: range_stat(gc.CORE_ARCHER_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_ARCHER_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_ARCHER_MOVEMENT_SPEED:.1f} units per second",
                StatType.DAMAGE: f"{archer_damage:.0f} per hit ({archer_damage / gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_ARCHER_ATTACK_RANGE:.0f} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against slow melee units", "In a large group", "Behind other units"],
                "Weak when": ["Against fast units", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CORE_BARBARIAN:
        
        damage_multiplier = 1.0
        if unit_tier == UnitTier.ADVANCED:
            damage_multiplier = 1.5
        elif unit_tier == UnitTier.ELITE:
            damage_multiplier = 2.0
        
        barbarian_damage = gc.CORE_BARBARIAN_ATTACK_DAMAGE * damage_multiplier
        return UnitData(
            name="Barbarian",
            description=f"Barbarians are durable melee units that deal damage in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_BARBARIAN_HP),
                StatType.SPEED: speed_stat(gc.CORE_BARBARIAN_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(barbarian_damage / gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION, 1.5),
                StatType.RANGE: range_stat(gc.CORE_BARBARIAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_BARBARIAN_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_BARBARIAN_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{barbarian_damage} per hit ({barbarian_damage / gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION:.1f} per second) in a medium area",
                StatType.RANGE: f"{gc.CORE_BARBARIAN_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against groups of units", "In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "In one-on-one combat with stronger units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CORE_CAVALRY:
        cavalry_damage = gc.CORE_CAVALRY_ATTACK_DAMAGE
        if unit_tier == UnitTier.ADVANCED:
            cavalry_damage = gc.CORE_CAVALRY_ATTACK_DAMAGE * 1.5
        elif unit_tier == UnitTier.ELITE:
            cavalry_damage = gc.CORE_CAVALRY_ATTACK_DAMAGE * 2.0
        
        return UnitData(
            name="Cavalry",
            description="Cavalry are fast and durable, but have low damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_CAVALRY_HP),
                StatType.SPEED: speed_stat(gc.CORE_CAVALRY_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(cavalry_damage / gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_CAVALRY_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_CAVALRY_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_CAVALRY_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{cavalry_damage} per hit ({cavalry_damage / gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_CAVALRY_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against ranged units", "With other fast units", "Tanking damage"],
                "Weak when": ["Against stronger melee units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CORE_DUELIST:
        duelist_damage = gc.CORE_DUELIST_ATTACK_DAMAGE
        if unit_tier == UnitTier.ADVANCED:
            duelist_damage = gc.CORE_DUELIST_ATTACK_DAMAGE * 1.5
        elif unit_tier == UnitTier.ELITE:
            duelist_damage = gc.CORE_DUELIST_ATTACK_DAMAGE * 2.0
        
        return UnitData(
            name="Duelist",
            description="Duelists are fragile melee units that attack very quickly.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_DUELIST_HP),
                StatType.SPEED: speed_stat(gc.CORE_DUELIST_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(duelist_damage / gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_DUELIST_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_DUELIST_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_DUELIST_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{duelist_damage/7} per hit ({duelist_damage / gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_DUELIST_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against high health units", "In a large group", "Behind other units"],
                "Weak when": ["Against ranged units", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CORE_LONGBOWMAN:
        longbowman_damage = gc.CORE_LONGBOWMAN_ATTACK_DAMAGE
        if unit_tier == UnitTier.ADVANCED:
            longbowman_damage = gc.CORE_LONGBOWMAN_ATTACK_DAMAGE * 1.5
        elif unit_tier == UnitTier.ELITE:
            longbowman_damage = gc.CORE_LONGBOWMAN_ATTACK_DAMAGE * 2.0
        
        return UnitData(
            name="Longbowman",
            description="Longbowmen are ranged units that shoot powerful arrows over very long range.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_LONGBOWMAN_HP),
                StatType.DAMAGE: damage_stat(longbowman_damage / gc.CORE_LONGBOWMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_LONGBOWMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CORE_LONGBOWMAN_MOVEMENT_SPEED),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_LONGBOWMAN_HP} maximum health",
                StatType.DAMAGE: f"{longbowman_damage} per hit ({longbowman_damage / gc.CORE_LONGBOWMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_LONGBOWMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CORE_LONGBOWMAN_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against other ranged units", "Against slow melee units", "Against healing units"],
                "Weak when": ["Against fast melee units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CORE_SWORDSMAN:
        swordsman_damage = gc.CORE_SWORDSMAN_ATTACK_DAMAGE
        if unit_tier == UnitTier.ADVANCED:
            swordsman_damage = gc.CORE_SWORDSMAN_ATTACK_DAMAGE * 1.5
        elif unit_tier == UnitTier.ELITE:
            swordsman_damage = gc.CORE_SWORDSMAN_ATTACK_DAMAGE * 2.0
        
        return UnitData(
            name="Swordsman",
            description="Swordsmen are balanced melee units that deal high damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_SWORDSMAN_HP),
                StatType.SPEED: speed_stat(gc.CORE_SWORDSMAN_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(swordsman_damage / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CORE_SWORDSMAN_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_SWORDSMAN_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_SWORDSMAN_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{swordsman_damage} per hit ({swordsman_damage / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CORE_SWORDSMAN_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against high health units", "Against weaker melee units", "In a large group"],
                "Weak when": ["Against ranged units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CORE_WIZARD:
        wizard_damage = gc.CORE_WIZARD_ATTACK_DAMAGE
        if unit_tier == UnitTier.ADVANCED:
            wizard_damage = gc.CORE_WIZARD_ATTACK_DAMAGE * 1.5
        elif unit_tier == UnitTier.ELITE:
            wizard_damage = gc.CORE_WIZARD_ATTACK_DAMAGE * 2.0
        
        return UnitData(
            name="Wizard",
            description=f"Wizards shoot fireballs that damage allied and enemy units in a large <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gc.CORE_WIZARD_HP),
                StatType.SPEED: speed_stat(gc.CORE_WIZARD_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.CORE_WIZARD_ATTACK_DAMAGE / gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION, 2),
                StatType.RANGE: range_stat(gc.CORE_WIZARD_ATTACK_RANGE),
                StatType.UTILITY: None
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CORE_WIZARD_HP} maximum health",
                StatType.SPEED: f"{gc.CORE_WIZARD_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{wizard_damage} per hit ({wizard_damage / gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION:.1f} per second) in a large area",
                StatType.RANGE: f"{gc.CORE_WIZARD_ATTACK_RANGE} units",
                StatType.UTILITY: None
            },
            tips={
                "Strong when": ["Against large groups", "Against slow units"],
                "Weak when": ["Against fast melee units", "Allies are in the way", "Against high health units"],
            },
            modification_levels={
                StatType.DAMAGE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_BANNER_BEARER:
        banner_bearer_health = gc.CRUSADER_BANNER_BEARER_HP
        if unit_tier == UnitTier.ADVANCED:
            banner_bearer_health = gc.CRUSADER_BANNER_BEARER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            banner_bearer_health = gc.CRUSADER_BANNER_BEARER_HP * 2.0
        
        return UnitData(
            name="Banner Bearer",
            description=f"Banner Bearers are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> with an <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts damage and movement speed.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(banner_bearer_health),
                StatType.SPEED: speed_stat(gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED),
                StatType.UTILITY: 8
            },
            tooltips={
                StatType.DEFENSE: f"{banner_bearer_health} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: f"Aura grants +{int(gc.CRUSADER_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE * 100)}% damage to allies and sets their movement speed to {gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second in a radius of {gc.CRUSADER_BANNER_BEARER_AURA_RADIUS}"
            },
            tips={
                "Strong when": ["In a large group", "With slow allies", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
                "Weak when": [f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_BLACK_KNIGHT:
        black_knight_health = gc.CRUSADER_BLACK_KNIGHT_HP
        if unit_tier == UnitTier.ADVANCED:
            black_knight_health = gc.CRUSADER_BLACK_KNIGHT_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            black_knight_health = gc.CRUSADER_BLACK_KNIGHT_HP * 2.0
        
        return UnitData(
            name="Black Knight",
            description=f"Black Knights are fast, <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that cause nearby units to <a href='{GlossaryEntryType.FLEE.value}'>Flee</a> on <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blows</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(black_knight_health, armored=True),
                StatType.SPEED: speed_stat(gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION),
                StatType.UTILITY: 7,
                StatType.RANGE: range_stat(gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{black_knight_health} maximum health, armored",
                StatType.SPEED: f"{gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE} per hit ({gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.UTILITY: "Nearby units flee on killing blow",
                StatType.RANGE: f"{gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE} units"
            },
            tips={
                "Strong when": ["Against low health units", "Able to kill multiple units quickly", "Against units with low damage per hit"],
                "Weak when": ["Walking through enemies to get to targets", "Against stronger melee units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_CATAPULT:
        catapult_health = gc.CRUSADER_CATAPULT_HP
        if unit_tier == UnitTier.ADVANCED:
            catapult_health = gc.CRUSADER_CATAPULT_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            catapult_health = gc.CRUSADER_CATAPULT_HP * 2.0
        
        return UnitData(
            name="Catapult",
            description=f"Catapults are immobile ranged units that deal high damage to all units in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(catapult_health),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_CATAPULT_DAMAGE / gc.CRUSADER_CATAPULT_COOLDOWN, 3),
                StatType.RANGE: range_stat(gc.CRUSADER_CATAPULT_MAXIMUM_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{catapult_health} maximum health",
                StatType.DAMAGE: f"{gc.CRUSADER_CATAPULT_DAMAGE} per hit ({gc.CRUSADER_CATAPULT_DAMAGE / gc.CRUSADER_CATAPULT_COOLDOWN:.1f} per second) in a medium area",
                StatType.RANGE: f"Between {gc.CRUSADER_CATAPULT_MINIMUM_RANGE} and {gc.CRUSADER_CATAPULT_MAXIMUM_RANGE} units"
            },
            tips={
                "Strong when": ["Against clustered groups", "Against slow units"],
                "Weak when": ["Against fast units", "Against spread out units", "Enemy units are too close", "Allies are in the way"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_CLERIC:
        cleric_health = gc.CRUSADER_CLERIC_HP
        if unit_tier == UnitTier.ADVANCED:
            cleric_health = gc.CRUSADER_CLERIC_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            cleric_health = gc.CRUSADER_CLERIC_HP * 2.0
        
        return UnitData(
            name="Healer",
            description=f"Healers are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> that heal the most damaged ally in range.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(cleric_health),
                StatType.SPEED: speed_stat(gc.CRUSADER_CLERIC_MOVEMENT_SPEED),
                StatType.UTILITY: damage_stat(gc.CRUSADER_CLERIC_HEALING / gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_CLERIC_ATTACK_RANGE),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_CLERIC_HEALING / gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION)
            },
            tooltips={
                StatType.DEFENSE: f"{gc.CRUSADER_CLERIC_HP} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_CLERIC_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: f"{gc.CRUSADER_CLERIC_HEALING} health per cast, {gc.CRUSADER_CLERIC_HEALING / gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION:.1f} per second",
                StatType.RANGE: f"{gc.CRUSADER_CLERIC_ATTACK_RANGE} units"
            },
            tips={
                "Strong when": ["In a large group", f"Allies are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a>", "Against units with low damage per second"],
                "Weak when": ["Against units with high damage per second", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
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
            },
            tooltips={
                StatType.DEFENSE: f"{commander_health} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_COMMANDER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.CRUSADER_COMMANDER_ATTACK_DAMAGE} per hit ({gc.CRUSADER_COMMANDER_ATTACK_DAMAGE / gc.CRUSADER_COMMANDER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.UTILITY: f"Aura grants +{int(gc.CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE * 100)}% damage to allies in a radius of {gc.CRUSADER_COMMANDER_AURA_RADIUS}",
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
        crossbowman_health = gc.CRUSADER_CROSSBOWMAN_HP
        if unit_tier == UnitTier.ADVANCED:
            crossbowman_health = gc.CRUSADER_CROSSBOWMAN_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            crossbowman_health = gc.CRUSADER_CROSSBOWMAN_HP * 2.0
        
        return UnitData(
            name="Crossbowman",
            description=f"Crossbowmen are medium-ranged <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that need to reload.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(crossbowman_health, armored=True),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE / (gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION + gc.CRUSADER_CROSSBOWMAN_ANIMATION_RELOAD_DURATION/2)),
                StatType.RANGE: range_stat(gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_CROSSBOWMAN_MOVEMENT_SPEED),
            },
            tooltips={
                StatType.DEFENSE: f"{crossbowman_health} maximum health, armored",
                StatType.DAMAGE: f"{gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE} per hit ({gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE / (gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION):.1f} per second while attacking, {gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE / (gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION + gc.CRUSADER_CROSSBOWMAN_ANIMATION_RELOAD_DURATION/2):.1f} per second including reloading). Starts with {gc.CRUSADER_CROSSBOWMAN_STARTING_AMMO} ammo, and can reload to regain ammo, up to {gc.CRUSADER_CROSSBOWMAN_MAX_AMMO}.",
                StatType.RANGE: f"{gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_CROSSBOWMAN_MOVEMENT_SPEED} units per second"
            },
            tips={
                "Strong when": ["Able to reload between fights", "Against units with low health", "In a large group", "Against units with low damage per hit"],
                "Weak when": ["Against long-ranged units", "Against fast units", "Reloading"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_DEFENDER:
        defender_health = gc.CRUSADER_DEFENDER_HP
        if unit_tier == UnitTier.ADVANCED:
            defender_health = gc.CRUSADER_DEFENDER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            defender_health = gc.CRUSADER_DEFENDER_HP * 2.0
        
        return UnitData(
            name="Defender",
            description=f"Defenders are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units with high health and low damage.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(defender_health, armored=True),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_DEFENDER_ATTACK_DAMAGE / gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_DEFENDER_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_DEFENDER_MOVEMENT_SPEED)
            },
            tooltips={
                StatType.DEFENSE: f"{defender_health} maximum health, armored",
                StatType.DAMAGE: f"{gc.CRUSADER_DEFENDER_ATTACK_DAMAGE} per hit ({gc.CRUSADER_DEFENDER_ATTACK_DAMAGE / gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_DEFENDER_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_DEFENDER_MOVEMENT_SPEED} units per second"
            },
            tips={
                "Strong when": ["Tanking damage", "Against units with low damage per hit", "Supported by healing units"],
                "Weak when": ["Against more powerful melee units", "Against ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_GOLD_KNIGHT:
        gold_knight_health = gc.CRUSADER_GOLD_KNIGHT_HP
        if unit_tier == UnitTier.ADVANCED:
            gold_knight_health = gc.CRUSADER_GOLD_KNIGHT_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            gold_knight_health = gc.CRUSADER_GOLD_KNIGHT_HP * 2.0
        
        return UnitData(
            name="Gold Knight",
            description=f"Gold Knights are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units with very fast <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> attacks that heal per enemy hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(gold_knight_health, armored=True, self_heal_dps=gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION * 1.5),
                StatType.SPEED: speed_stat(gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION, 1.5),
                StatType.RANGE: range_stat(gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{gold_knight_health} maximum health, armored. Heals {gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL} per enemy hit ({gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per enemy per second)",
                StatType.SPEED: f"{gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE} per hit, {gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second in a medium area",
                StatType.RANGE: f"{gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE} units"
            },
            tips={
                "Strong when": ["Against melee units","Against large groups", "Against units with low damage per hit", "Supported by healing units", "Spreading out incoming damage"],
                "Weak when": ["Against ranged units", "Against stronger melee units", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units", "Overwhelmed by high damage"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_GUARDIAN_ANGEL:
        guardian_angel_health = gc.CRUSADER_GUARDIAN_ANGEL_HP
        if unit_tier == UnitTier.ADVANCED:
            guardian_angel_health = gc.CRUSADER_GUARDIAN_ANGEL_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            guardian_angel_health = gc.CRUSADER_GUARDIAN_ANGEL_HP * 2.0
        
        return UnitData(
            name="Guardian Angel",
            description=f"Guardian Angels are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> that continuously heal the ally they are following.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(guardian_angel_health),
                StatType.SPEED: speed_stat(gc.CRUSADER_GUARDIAN_ANGEL_MOVEMENT_SPEED),
                StatType.UTILITY: damage_stat(gc.CRUSADER_GUARDIAN_ANGEL_HEALING / gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN),
                StatType.RANGE: range_stat(gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE)
            },
            tooltips={
                StatType.DEFENSE: f"{guardian_angel_health} maximum health",
                StatType.SPEED: f"{gc.CRUSADER_GUARDIAN_ANGEL_MOVEMENT_SPEED} units per second",
                StatType.UTILITY: f"{gc.CRUSADER_GUARDIAN_ANGEL_HEALING} health per cast, {gc.CRUSADER_GUARDIAN_ANGEL_HEALING / gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN:.1f} per second",
                StatType.RANGE: f"{gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE} units"
            },
            tips={
                "Strong when": [f"Supporting an <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> unit", "Supporting ally against a single low-damage enemy"],
                "Weak when": [f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>", "Following a unit that is full health"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_PALADIN:
        paladin_health = gc.CRUSADER_PALADIN_HP
        if unit_tier == UnitTier.ADVANCED:
            paladin_health = gc.CRUSADER_PALADIN_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            paladin_health = gc.CRUSADER_PALADIN_HP * 2.0
        
        return UnitData(
            name="Paladin",
            description=f"Paladins are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can heal themselves.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(paladin_health, self_heal_dps=gc.CRUSADER_PALADIN_SKILL_HEAL / gc.CRUSADER_PALADIN_SKILL_COOLDOWN, armored=True),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_PALADIN_ATTACK_DAMAGE / gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_PALADIN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_PALADIN_MOVEMENT_SPEED)
            },
            tooltips={
                StatType.DEFENSE: f"{paladin_health} maximum health, armored. Heals for {gc.CRUSADER_PALADIN_SKILL_HEAL} per cast ({gc.CRUSADER_PALADIN_SKILL_HEAL / gc.CRUSADER_PALADIN_SKILL_COOLDOWN:.1f} per second)",
                StatType.DAMAGE: f"{gc.CRUSADER_PALADIN_ATTACK_DAMAGE} per hit ({gc.CRUSADER_PALADIN_ATTACK_DAMAGE / gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_PALADIN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_PALADIN_MOVEMENT_SPEED} units per second"
            },
            tips={
                "Strong when": ["Tanking damage", "Against units with low damage per hit", "In one-on-one fights", "Supported by healing units"],
                "Weak when": ["Against units with high damage per hit", "Against units with high damage per second", "Against large groups"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.CRUSADER_PIKEMAN:
        pikeman_health = gc.CRUSADER_PIKEMAN_HP
        if unit_tier == UnitTier.ADVANCED:
            pikeman_health = gc.CRUSADER_PIKEMAN_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            pikeman_health = gc.CRUSADER_PIKEMAN_HP * 2.0
        
        return UnitData(
            name="Pikeman",
            description=f"Pikemen are melee units with high damage and long reach.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(pikeman_health),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE / gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_PIKEMAN_ATTACK_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED)
            },
            tooltips={
                StatType.DEFENSE: f"{pikeman_health} maximum health",
                StatType.DAMAGE: f"{gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE} per hit ({gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE / gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_PIKEMAN_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED} units per second"
            },
            tips={
                "Strong when": [f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units", "In a large group", "Behind other units"],
                "Weak when": ["Against ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
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
                StatType.SPEED: speed_stat(gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED)
            },
            tooltips={
                StatType.DEFENSE: f"{red_knight_health} maximum health, armored",
                StatType.DAMAGE: f"{gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE} per hit ({gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_RED_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED} units per second"
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
        soldier_health = gc.CRUSADER_SOLDIER_HP
        if unit_tier == UnitTier.ADVANCED:
            soldier_health = gc.CRUSADER_SOLDIER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            soldier_health = gc.CRUSADER_SOLDIER_HP * 2.0
        
        return UnitData(
            name="Soldier",
            description=f"Soliders are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units that can switch between melee and ranged attacks.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(soldier_health, armored=True),
                StatType.DAMAGE: damage_stat(gc.CRUSADER_SOLDIER_MELEE_DAMAGE / gc.CRUSADER_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.CRUSADER_SOLDIER_RANGED_RANGE),
                StatType.SPEED: speed_stat(gc.CRUSADER_SOLDIER_MOVEMENT_SPEED)
            },
            tooltips={
                StatType.DEFENSE: f"{soldier_health} maximum health, armored",
                StatType.DAMAGE: f"Melee: {gc.CRUSADER_SOLDIER_MELEE_DAMAGE} per hit ({gc.CRUSADER_SOLDIER_MELEE_DAMAGE / gc.CRUSADER_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION:.1f} per second), Ranged: {gc.CRUSADER_SOLDIER_RANGED_DAMAGE} per hit ({gc.CRUSADER_SOLDIER_RANGED_DAMAGE / gc.CRUSADER_SOLDIER_ANIMATION_RANGED_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"Melee: {gc.CRUSADER_SOLDIER_MELEE_RANGE} units, Ranged: {gc.CRUSADER_SOLDIER_RANGED_RANGE} units",
                StatType.SPEED: f"{gc.CRUSADER_SOLDIER_MOVEMENT_SPEED} units per second"
            },
            tips={
                "Strong when": ["Can weaken melee enemies with ranged attacks", "Against units with low damage per hit"],
                "Weak when": ["Against stronger melee units or ranged units"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    if unit_type == UnitType.ZOMBIE_BASIC_ZOMBIE:
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
        if unit_tier == UnitTier.ADVANCED:
            zombie_brute_health = gc.ZOMBIE_BRUTE_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_brute_health = gc.ZOMBIE_BRUTE_HP * 2.0
        
        return UnitData(
            name="Brute",
            description=f"Brutes are slow melee units that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and carry two <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> into battle.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_brute_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_BRUTE_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_BRUTE_ATTACK_DAMAGE / gc.ZOMBIE_BRUTE_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_BRUTE_ATTACK_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_brute_health} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_BRUTE_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_BRUTE_ATTACK_DAMAGE} per hit ({gc.ZOMBIE_BRUTE_ATTACK_DAMAGE / gc.ZOMBIE_BRUTE_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.ZOMBIE_BRUTE_ATTACK_RANGE} units",
                StatType.UTILITY: "Infects enemies on hit, carries two Zombies into battle"
            },
            tips={
                "Strong when": ["Against many weak enemies", "In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "Against units with high damage per second", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_BRUTE:
        if unit_tier == UnitTier.ADVANCED:
            zombie_brute_health = gc.ZOMBIE_BRUTE_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_brute_health = gc.ZOMBIE_BRUTE_HP * 2.0
        
        return UnitData(
            name="Brute",
            description=f"Brutes are slow melee units that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and carry two <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>Zombies</a> into battle.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_brute_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_BRUTE_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_BRUTE_ATTACK_DAMAGE / gc.ZOMBIE_BRUTE_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_BRUTE_ATTACK_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_brute_health} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_BRUTE_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_BRUTE_ATTACK_DAMAGE} per hit ({gc.ZOMBIE_BRUTE_ATTACK_DAMAGE / gc.ZOMBIE_BRUTE_ANIMATION_ATTACK_DURATION:.1f} per second)",
                StatType.RANGE: f"{gc.ZOMBIE_BRUTE_ATTACK_RANGE} units",
                StatType.UTILITY: "Infects enemies on hit, carries two Zombies into battle"
            },
            tips={
                "Strong when": ["Against many weak enemies", "In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "Against units with high damage per second", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_GRABBER:
        if unit_tier == UnitTier.ADVANCED:
            zombie_grabber_health = gc.ZOMBIE_GRABBER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_grabber_health = gc.ZOMBIE_GRABBER_HP * 2.0
        
        return UnitData(
            name="Grabber",
            description=f"Grabbers are slow melee units with long reach that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and can grab and pull enemies towards them.",
            tier=unit_tier,
            stats={ 
                StatType.DEFENSE: defense_stat(zombie_grabber_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_GRABBER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_GRABBER_ATTACK_DAMAGE / gc.ZOMBIE_GRABBER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_GRABBER_GRAB_MAXIMUM_RANGE),
                StatType.UTILITY: 7.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_grabber_health} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_GRABBER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_GRABBER_ATTACK_DAMAGE} per hit ({gc.ZOMBIE_GRABBER_ATTACK_DAMAGE / gc.ZOMBIE_GRABBER_ANIMATION_ATTACK_DURATION:.1f} per second), Grab deals {gc.ZOMBIE_GRABBER_GRAB_DAMAGE} per hit with a {gc.ZOMBIE_GRABBER_GRAB_COOLDOWN} second cooldown",
                StatType.RANGE: f"Melee: {gc.ZOMBIE_GRABBER_ATTACK_RANGE} units, Grab: {gc.ZOMBIE_GRABBER_GRAB_MINIMUM_RANGE} to {gc.ZOMBIE_GRABBER_GRAB_MAXIMUM_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit, can grab and pull enemies towards them"
            },
            tips={
                "Strong when": ["Pulling enemy units into a group of allies", "In a large group", "Behind other units", "Against ranged units"],
                "Weak when": ["In one-on-one combat", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            },
            modification_levels={
                StatType.DEFENSE: 1 if unit_tier == UnitTier.ADVANCED else 2 if unit_tier == UnitTier.ELITE else 0
            }
        )
    
    if unit_type == UnitType.ZOMBIE_JUMPER:
        if unit_tier == UnitTier.ADVANCED:
            zombie_jumper_health = gc.ZOMBIE_JUMPER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_jumper_health = gc.ZOMBIE_JUMPER_HP * 2.0
        
        return UnitData(
            name="Jumper",
            description=f"Jumpers are fast, high damage <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit and can jump to their target.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_jumper_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_JUMPER_MOVEMENT_SPEED) + 2,
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_JUMPER_ATTACK_DAMAGE / gc.ZOMBIE_JUMPER_ANIMATION_ATTACK_DURATION),
                StatType.RANGE: range_stat(gc.ZOMBIE_JUMPER_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            }, 
            tooltips={
                StatType.DEFENSE: f"{zombie_jumper_health} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_JUMPER_MOVEMENT_SPEED} units per second, can jump {gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE} units every {gc.ZOMBIE_JUMPER_JUMP_COOLDOWN} seconds",
                StatType.DAMAGE: f"{gc.ZOMBIE_JUMPER_ATTACK_DAMAGE} per hit ({gc.ZOMBIE_JUMPER_ATTACK_DAMAGE / gc.ZOMBIE_JUMPER_ANIMATION_ATTACK_DURATION:.1f} per second). Jump deals {gc.ZOMBIE_JUMPER_JUMP_DAMAGE} damage with a {gc.ZOMBIE_JUMPER_JUMP_COOLDOWN} second cooldown",
                StatType.RANGE: f"Melee: {gc.ZOMBIE_JUMPER_ATTACK_RANGE} units, Jump: {gc.ZOMBIE_JUMPER_MINIMUM_JUMP_RANGE} to {gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["Against individual weak enemies", "Enemies are distracted", "Against ranged units"],
                "Weak when": ["Against stronger melee units", "Against fast melee units"],
            }
        )
    
    if unit_type == UnitType.ZOMBIE_SPITTER:
        if unit_tier == UnitTier.ADVANCED:
            zombie_spitter_health = gc.ZOMBIE_SPITTER_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_spitter_health = gc.ZOMBIE_SPITTER_HP * 2.0
        
        return UnitData(
            name="Spitter",
            description=f"Spitters are slow, short-ranged <a href='{GlossaryEntryType.SPREADER.value}'>Spreaders</a> that <a href='{GlossaryEntryType.POISON.value}'>Poison</a> and <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> on hit.",
            tier=unit_tier,
            stats={
                StatType.DEFENSE: defense_stat(zombie_spitter_health),
                StatType.SPEED: speed_stat(gc.ZOMBIE_SPITTER_MOVEMENT_SPEED),
                StatType.DAMAGE: damage_stat(gc.ZOMBIE_SPITTER_ATTACK_DAMAGE / gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION, 2/3),
                StatType.RANGE: range_stat(gc.ZOMBIE_SPITTER_ATTACK_RANGE),
                StatType.UTILITY: 2.5
            },
            tooltips={
                StatType.DEFENSE: f"{zombie_spitter_health} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_SPITTER_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_SPITTER_ATTACK_DAMAGE} poison damage ({gc.ZOMBIE_SPITTER_ATTACK_DAMAGE/gc.ZOMBIE_INFECTION_DURATION} damage per second per poison) ({gc.ZOMBIE_SPITTER_ATTACK_DAMAGE / gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION:.1f} per second if poisoning multiple enemies)",
                StatType.RANGE: f"{gc.ZOMBIE_SPITTER_ATTACK_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["Against many weak enemies", "In a large group", "Behind other units"],
                "Weak when": ["Against melee units", "Against long ranged units", "Against a small number of units", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
            }
        )
    
    if unit_type == UnitType.ZOMBIE_TANK:
        if unit_tier == UnitTier.ADVANCED:
            zombie_tank_health = gc.ZOMBIE_TANK_HP * 1.5
        elif unit_tier == UnitTier.ELITE:
            zombie_tank_health = gc.ZOMBIE_TANK_HP * 2.0
        
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
                StatType.DEFENSE: f"{zombie_tank_health} maximum health",
                StatType.SPEED: f"{gc.ZOMBIE_TANK_MOVEMENT_SPEED} units per second",
                StatType.DAMAGE: f"{gc.ZOMBIE_TANK_ATTACK_DAMAGE} per hit, {gc.ZOMBIE_TANK_ATTACK_DAMAGE / gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION:.1f} per second + infection",
                StatType.RANGE: f"{gc.ZOMBIE_TANK_ATTACK_RANGE} units",
                StatType.UTILITY: f"Infects enemies on hit"
            },
            tips={
                "Strong when": ["In a large group", "Tanking damage"],
                "Weak when": ["Against ranged units", "Against units with high damage per second"],
            }
        )
    
    if unit_type == UnitType.WEREBEAR:
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
            }
        )
    raise ValueError(f"Unknown unit type: {unit_type}")