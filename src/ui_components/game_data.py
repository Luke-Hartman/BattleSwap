import enum
from components.unit_type import UnitType
from game_constants import gc

def taper(value: float) -> float:
    """Tapers the value to a stat value between 1 and 10, with a steeper curve at the end."""
    if value < 7:
        return value
    return 7 + min((value - 7)**0.5, 3)

def damage_stat(dps: float, multiplier: float = 1) -> float:
    """Maps damage to a stat value between 1 and 10."""
    stat = (dps * multiplier) / (gc.CORE_SWORDSMAN_ATTACK_DAMAGE / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION) * 6
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
    stat = range / gc.CORE_ARCHER_ATTACK_RANGE * 5
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

# Unit data
UNIT_DATA = {
    UnitType.CORE_ARCHER: {
        "name": "Archer",
        "description": "Archers are basic ranged units that deal damage from a distance.",
        "stats": {
            StatType.DAMAGE: damage_stat(gc.CORE_ARCHER_ATTACK_DAMAGE / gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION),
            StatType.DEFENSE: defense_stat(gc.CORE_ARCHER_HP),
            StatType.SPEED: speed_stat(gc.CORE_ARCHER_MOVEMENT_SPEED),
            StatType.RANGE: range_stat(gc.CORE_ARCHER_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DAMAGE: f"{gc.CORE_ARCHER_ATTACK_DAMAGE} per hit ({gc.CORE_ARCHER_ATTACK_DAMAGE / gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION:.1f} per second)",
            StatType.DEFENSE: f"{gc.CORE_ARCHER_HP} maximum health",
            StatType.SPEED: f"{gc.CORE_ARCHER_MOVEMENT_SPEED} units per second",
            StatType.RANGE: f"{gc.CORE_ARCHER_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against slow melee units", "In a large group", "Behind other units"],
            "Weak when": ["Against fast units", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
        }
    },
    UnitType.CORE_BARBARIAN: {
        "name": "Barbarian",
        "description": f"Barbarians are durable melee units that deal damage in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CORE_BARBARIAN_HP),
            StatType.SPEED: speed_stat(gc.CORE_BARBARIAN_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CORE_BARBARIAN_ATTACK_DAMAGE / gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION, 1.5),
            StatType.RANGE: range_stat(gc.CORE_BARBARIAN_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CORE_BARBARIAN_HP} maximum health",
            StatType.SPEED: f"{gc.CORE_BARBARIAN_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CORE_BARBARIAN_ATTACK_DAMAGE} per hit ({gc.CORE_BARBARIAN_ATTACK_DAMAGE / gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION:.1f} per second) in a medium area",
            StatType.RANGE: f"{gc.CORE_BARBARIAN_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against groups of units", "In a large group", "Tanking damage"],
            "Weak when": ["Against ranged units", "In one-on-one combat with stronger units"],
        }
    },
    UnitType.CORE_CAVALRY: {
        "name": "Cavalry",
        "description": "Cavalry are fast and durable, but have low damage.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CORE_CAVALRY_HP),
            StatType.SPEED: speed_stat(gc.CORE_CAVALRY_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CORE_CAVALRY_ATTACK_DAMAGE / gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION),
            StatType.RANGE: range_stat(gc.CORE_CAVALRY_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CORE_CAVALRY_HP} maximum health",
            StatType.SPEED: f"{gc.CORE_CAVALRY_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CORE_CAVALRY_ATTACK_DAMAGE} per hit ({gc.CORE_CAVALRY_ATTACK_DAMAGE / gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION:.1f} per second)",
            StatType.RANGE: f"{gc.CORE_CAVALRY_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against ranged units", "With other fast units", "Tanking damage"],
            "Weak when": ["Against stronger melee units"],
        }
    },
    UnitType.CORE_DUELIST: {
        "name": "Duelist",
        "description": "Duelists are fragile melee units that attack very quickly.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CORE_DUELIST_HP),
            StatType.SPEED: speed_stat(gc.CORE_DUELIST_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CORE_DUELIST_ATTACK_DAMAGE / gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION),
            StatType.RANGE: range_stat(gc.CORE_DUELIST_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CORE_DUELIST_HP} maximum health",
            StatType.SPEED: f"{gc.CORE_DUELIST_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CORE_DUELIST_ATTACK_DAMAGE/7} per hit ({gc.CORE_DUELIST_ATTACK_DAMAGE / gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION:.1f} per second)",
            StatType.RANGE: f"{gc.CORE_DUELIST_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against high health units", "In a large group", "Behind other units"],
            "Weak when": ["Against ranged units", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
        }
    },
    UnitType.CORE_LONGBOWMAN: {
        "name": "Longbowman",
        "description": "Longbowmen are ranged units that shoot powerful arrows over very long range.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CORE_LONGBOWMAN_HP),
            StatType.DAMAGE: damage_stat(gc.CORE_LONGBOWMAN_ATTACK_DAMAGE / gc.CORE_LONGBOWMAN_ANIMATION_ATTACK_DURATION),
            StatType.RANGE: range_stat(gc.CORE_LONGBOWMAN_ATTACK_RANGE),
            StatType.SPEED: speed_stat(gc.CORE_LONGBOWMAN_MOVEMENT_SPEED)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CORE_LONGBOWMAN_HP} maximum health",
            StatType.DAMAGE: f"{gc.CORE_LONGBOWMAN_ATTACK_DAMAGE} per hit ({gc.CORE_LONGBOWMAN_ATTACK_DAMAGE / gc.CORE_LONGBOWMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
            StatType.RANGE: f"{gc.CORE_LONGBOWMAN_ATTACK_RANGE} units",
            StatType.SPEED: f"{gc.CORE_LONGBOWMAN_MOVEMENT_SPEED} units per second"
        },
        "tips": {
            "Strong when": ["Against other ranged units", "Against slow melee units", "Against healing units"],
            "Weak when": ["Against fast melee units"],
        }
    },
    UnitType.CORE_SWORDSMAN: {
        "name": "Swordsman",
        "description": "Swordsmen are balanced melee units that deal high damage.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CORE_SWORDSMAN_HP),
            StatType.SPEED: speed_stat(gc.CORE_SWORDSMAN_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CORE_SWORDSMAN_ATTACK_DAMAGE / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION),
            StatType.RANGE: range_stat(gc.CORE_SWORDSMAN_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CORE_SWORDSMAN_HP} maximum health",
            StatType.SPEED: f"{gc.CORE_SWORDSMAN_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CORE_SWORDSMAN_ATTACK_DAMAGE} per hit ({gc.CORE_SWORDSMAN_ATTACK_DAMAGE / gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION:.1f} per second)",
            StatType.RANGE: f"{gc.CORE_SWORDSMAN_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against high health units", "Against weaker melee units", "In a large group"],
            "Weak when": ["Against ranged units"],
        }
    },
    UnitType.CORE_WIZARD: {
        "name": "Wizard",
        "description": f"Wizards shoot powerful fireballs that damage both allied and enemy units in a large <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CORE_WIZARD_HP),
            StatType.SPEED: speed_stat(gc.CORE_WIZARD_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CORE_WIZARD_ATTACK_DAMAGE / gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION, 2),
            StatType.RANGE: range_stat(gc.CORE_WIZARD_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CORE_WIZARD_HP} maximum health",
            StatType.SPEED: f"{gc.CORE_WIZARD_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CORE_WIZARD_ATTACK_DAMAGE} per hit ({gc.CORE_WIZARD_ATTACK_DAMAGE / gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION:.1f} per second) in a large area",
            StatType.RANGE: f"{gc.CORE_WIZARD_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against large groups", "Against slow units"],
            "Weak when": ["Against fast melee units", "Allies are in the way", "Against high health units"],
        }
    },
    UnitType.CRUSADER_BLACK_KNIGHT: {
        "name": "Black Knight",
        "description": f"Black Knights are fast, <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that cause nearby units to <a href='{GlossaryEntryType.FLEE.value}'>Flee</a> on <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blows</a>.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CRUSADER_BLACK_KNIGHT_HP, armored=True),
            StatType.SPEED: speed_stat(gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION),
            StatType.UTILITY: 7,
            StatType.RANGE: range_stat(gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CRUSADER_BLACK_KNIGHT_HP} maximum health, armored",
            StatType.SPEED: f"{gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE} per hit ({gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second)",
            StatType.UTILITY: "Nearby units flee on killing blow",
            StatType.RANGE: f"{gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against low health units", "Able to kill multiple units quickly", "Against units with low damage per hit"],
            "Weak when": ["Walking through enemies to get to targets", "Against stronger melee units"],
        }
    },
    UnitType.CRUSADER_GOLD_KNIGHT: {
        "name": "Gold Knight",
        "description": f"Gold Knights are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units with very fast <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> attacks that heal per enemy hit.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CRUSADER_GOLD_KNIGHT_HP, armored=True, self_heal_dps=gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION * 1.5),
            StatType.SPEED: speed_stat(gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION, 1.5),
            StatType.RANGE: range_stat(gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CRUSADER_GOLD_KNIGHT_HP} maximum health, armored. Heals {gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL} per enemy hit ({gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per enemy per second)",
            StatType.SPEED: f"{gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE} per hit, {gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second",
            StatType.RANGE: f"{gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against melee units","Against large groups", "Against units with low damage per hit", "Supported by healing units", "Spreading out incoming damage"],
            "Weak when": ["Against ranged units", "Against stronger melee units", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units", "Overwhelmed by high damage"],
        }
    },
    UnitType.CRUSADER_CLERIC: {
        "name": "Healer",
        "description": f"Healers are <a href='{GlossaryEntryType.FOLLOWER.value}'>Followers</a> that heal the most damaged ally in range.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CRUSADER_CLERIC_HP),
            StatType.SPEED: speed_stat(gc.CRUSADER_CLERIC_MOVEMENT_SPEED),
            StatType.UTILITY: 9,
            StatType.RANGE: range_stat(gc.CRUSADER_CLERIC_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CRUSADER_CLERIC_HP} maximum health",
            StatType.SPEED: f"{gc.CRUSADER_CLERIC_MOVEMENT_SPEED} units per second",
            StatType.UTILITY: f"{gc.CRUSADER_CLERIC_HEALING} health per cast, {gc.CRUSADER_CLERIC_HEALING / gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION:.1f} per second",
            StatType.RANGE: f"{gc.CRUSADER_CLERIC_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["In a large group", f"Allies are <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a>", "Against units with low damage per second"],
            "Weak when": ["Against units with high damage per second", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
        }
    },
    UnitType.ZOMBIE_BASIC_ZOMBIE: {
        "name": "Zombie",
        "description": f"Zombies are weak melee units that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> enemies on hit.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.ZOMBIE_BASIC_ZOMBIE_HP),
            StatType.SPEED: speed_stat(gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE / gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.ZOMBIE_BASIC_ZOMBIE_HP} maximum health",
            StatType.SPEED: f"{gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE} per hit, {gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE / gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION:.1f} per second + infection"
        },
        "tips": {
            "Strong when": ["In a large group", "Against many weak enemies", "Tanking damage"],
            "Weak when": ["Against ranged units", "Against units with high damage per second", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
        }
    },
    UnitType.ZOMBIE_SPITTER: {
        "name": "Spitter",
        "description": f"Spitters are short-ranged <a href='{GlossaryEntryType.SPREADER.value}'>Spreaders</a> that <a href='{GlossaryEntryType.POISON.value}'>Poison</a> and <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> enemies.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.ZOMBIE_SPITTER_HP),
            StatType.SPEED: speed_stat(gc.ZOMBIE_SPITTER_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.ZOMBIE_SPITTER_ATTACK_DAMAGE / gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION, 2/3),
            StatType.RANGE: range_stat(gc.ZOMBIE_SPITTER_ATTACK_RANGE)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.ZOMBIE_SPITTER_HP} maximum health",
            StatType.SPEED: f"{gc.ZOMBIE_SPITTER_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.ZOMBIE_SPITTER_ATTACK_DAMAGE} poison damage, {gc.ZOMBIE_SPITTER_ATTACK_DAMAGE / gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION:.1f} per second",
            StatType.RANGE: f"{gc.ZOMBIE_SPITTER_ATTACK_RANGE} units"
        },
        "tips": {
            "Strong when": ["Against many weak enemies", "In a large group", "Behind other units"],
            "Weak when": ["Against melee units", "Against long ranged units", "Against a small number of units", f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>"],
        }
    },
    UnitType.ZOMBIE_TANK: {
        "name": "Tank",
        "description": f"Tanks are massive melee units with high health that <a href='{GlossaryEntryType.INFECTION.value}'>Infect</a> enemies on hit.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.ZOMBIE_TANK_HP),
            StatType.SPEED: speed_stat(gc.ZOMBIE_TANK_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.ZOMBIE_TANK_ATTACK_DAMAGE / gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION)
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.ZOMBIE_TANK_HP} maximum health",
            StatType.SPEED: f"{gc.ZOMBIE_TANK_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.ZOMBIE_TANK_ATTACK_DAMAGE} per hit, {gc.ZOMBIE_TANK_ATTACK_DAMAGE / gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION:.1f} per second + infection"
        },
        "tips": {
            "Strong when": ["In a large group", "Tanking damage"],
            "Weak when": ["Against ranged units", "Against units with high damage per second"],
        }
    },
    UnitType.CRUSADER_BANNER_BEARER: {
        "name": "Banner Bearer",
        "description": f"Banner Bearers are support units with an <a href='{GlossaryEntryType.AURA.value}'>Aura</a> that boosts damage and movement speed.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CRUSADER_BANNER_BEARER_HP),
            StatType.SPEED: speed_stat(gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED),
            StatType.UTILITY: 8
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CRUSADER_BANNER_BEARER_HP} maximum health",
            StatType.SPEED: f"{gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second",
            StatType.UTILITY: f"Aura grants +{int(gc.CRUSADER_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE * 100)}% damage to allies and sets their movement speed to {gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second in a radius of {gc.CRUSADER_BANNER_BEARER_AURA_RADIUS}"
        },
        "tips": {
            "Strong when": ["In a large group", "With slow allies", f"Against <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> units"],
            "Weak when": [f"Against <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>", f"Against <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>"],
        }
    },
} 