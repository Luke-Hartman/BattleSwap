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
    ARMORED = "Armored"
    AREA_OF_EFFECT = "Area of Effect" 
    FLEE = "Flee"
    INFECTION = "Infection"
    HEALING = "Healing"
    IGNITE = "Ignite"
    AURA = "Aura"
    KILLING_BLOW = "Killing Blow"
    HUNTER = "Hunter"
    FOLLOWER = "Follower"
    POINTS = "Points"
    CORRUPTION = "Corruption"
    BARRACKS = "Barracks"
    FACTION = "Faction"

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
    GlossaryEntryType.CORRUPTION: f"Corruption reopens up to {gc.CORRUPTION_BATTLE_COUNT} battles you've already completed, with modifiers to increase their difficulty. To continue, you must defeat these corrupted battles again. Corruption can activate when you exceed {gc.CORRUPTION_TRIGGER_POINTS} <a href='{GlossaryEntryType.POINTS.value}'>points</a> in your <a href='{GlossaryEntryType.BARRACKS.value}'>{GlossaryEntryType.BARRACKS.value}</a>. Efficient players can corrupt and reconquer every battle.",
    GlossaryEntryType.FACTION: "Factions are groups of units that share a common theme. Enemy armies are made up of units from a specific faction plus the core units, while players are free to mix and match units from different factions.",
    GlossaryEntryType.FLEE: "Fleeing units move away from the source of the effect at a reduced speed for 2 seconds.",
    GlossaryEntryType.FOLLOWER: "Follower units follow a nearby friendly non-follower unit until it is killed.",
    GlossaryEntryType.HEALING: "Healing restores health to units, based on the specified healing amount.",
    GlossaryEntryType.HUNTER: "While most units target the nearest enemy unit, Hunters prioritize units with low current health.",
    GlossaryEntryType.INFECTION: f"Infected units turn into <a href='{UnitType.ZOMBIE_BASIC_ZOMBIE.value}'>zombies</a> when they die. Infection lasts for 2 seconds.",
    GlossaryEntryType.KILLING_BLOW: "A killing blow is when an instance of damage is enough to kill a unit. Some units have special abilities that trigger when they deal a killing blow.",
    GlossaryEntryType.POINTS: f"Points represent the value of a unit. When you have more than {gc.CORRUPTION_TRIGGER_POINTS} points of units in your <a href='{GlossaryEntryType.BARRACKS.value}'>Barracks</a>, <a href='{GlossaryEntryType.CORRUPTION.value}'>Corruption</a> will trigger.",
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
        "tips": [
            "Archers have low damage and health compared to melee units, but make up for it with their range.",
            "They are strong against slow melee units, as this gives them plenty of time to deal damage from a safe distance.",
            "However, archers are vulnerable to fast melee units, since there is less time to attack before being reached.",
            "They are also weak against units with longer range, which can pick them off before they can retaliate.",
            "Archers also pair well with durable melee units that can distract enemies while the Archers deal damage from a distance.",
            "Like many other units, archers are especially effective when used in groups.",
            f"Archers are particularly vulnerable to <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>."
            "Note that these tips also apply to many other ranged units."
        ]
    },
    UnitType.CORE_BARBARIAN: {
        "name": "Barbarian",
        "description": "Barbarians are durable melee units that deal damage in an <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
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
        "tips": [
            "Barbarians are good at both dealing damage and being durable, making them great frontline units.",
            "They are best against groups of units, as they deal <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> damage.",
            "However, they struggle against ranged units and in one-on-one combat with even stronger melee units.",
            "Note that Barbarian <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a> damage does not affect friendly units, so they work well with other melee units."
        ]
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
        "tips": [
            "Cavalry's high speed and health makes them perfect for closing the gap with ranged units.",
            "However, they have relatively low damage, making them less effective against more balanced melee units.",
            "Cavalry are very effective in large groups, as they can quickly overwhelm individual units that are spread out.",
            "Even though they have high speed, their relatively high health can make them a decent defensive unit.",
            "When improperly positioned, Cavalry can run ahead of the main group and get themselves killed."
        ]
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
        "tips": [
            "Duelists deal very high damage, but need to be protected by other units. They are best paired with other melee units that have shorter range that will draw the enemy's attention.",
            "Duelists are perfect when you need a lot of damage per second against a single target with high health.",
            f"Since Duelists deal damage over many hits, they are less effective against <a href='{GlossaryEntryType.ARMORED.value}'>{GlossaryEntryType.ARMORED.value}</a> units.",
            "Due to their low health, Duelists are vulnerable to ranged units, or being overwhelmed by other melee units.",
        ],
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
        "tips": [
            "Longbowmen are very good against exposed ranged units, as they can often outrange them.",
            "Compared to archers, they are relatively less efficient in terms of damage per second.",
            f"Though their high damage per hit also makes them efficient against <a href='{GlossaryEntryType.ARMORED.value}'>{GlossaryEntryType.ARMORED.value}</a> units.",
            "Since Longbowmen take so long to attack, it is important to ensure that they are hitting their target.",
            "Longbowmen can be used to burst down units that rapidly heal, as their damage is delivered all at once.",
        ]
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
        "tips": [
            "Swordsmen are very efficient at fighting other melee units in one-on-one combat or in small groups.",
            "Groups of swordsmen can deal incredibly high damage in a short period of time.",
            "Due to their relatively low speed and defense, swordsmen are vulnerable against ranged units.",
        ]
    },
    UnitType.CORE_WIZARD: {
        "name": "Wizard",
        "description": "Wizards shoot powerful fireballs that damage both allied and enemy units in a large <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
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
        "tips": [
            f"Wizards are best when they can hit many enemies at once, as their fireballs result in a large <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>Area of Effect</a>.",
            "Wizards also deal damage to allied units, so it requires careful positioning to maximize their damage output.",
            "It is often effective to position allied units to distract enemies, while the Wizards deal damage from a distance.",
            "When facing Wizards, you can often cause them to damage their teammates.",
            "Wizards are weak against high health or healing units which can ignore their relatively low single-target damage.",
        ]
    },
    UnitType.CRUSADER_BLACK_KNIGHT: {
        "name": "Black Knight",
        "description": f"Black Knights are fast, <a href='{GlossaryEntryType.ARMORED.value}'>Armored</a> <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a> that cause nearby units to <a href='{GlossaryEntryType.FLEE.value}'>{GlossaryEntryType.FLEE.value}</a> on <a href='{GlossaryEntryType.KILLING_BLOW.value}'>Killing Blows</a>.",
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
        "tips": [
            f"As <a href='{GlossaryEntryType.HUNTER.value}'>Hunters</a>, Black Knights can easily target units that are behind other units.",
            f"The <a href='{GlossaryEntryType.FLEE.value}'>Flee</a> effect creates an opportunity for Black Knights to kill more units, potentially leading to a chain of kills.",
            f"The <a href='{GlossaryEntryType.FLEE.value}'>Flee</a> effect also applies to allied units, making Black Knights less effective in groups of allied melee units.",
            f"Ranged units can take advantage of the chaos caused by Black Knights without being affected by the <a href='{GlossaryEntryType.FLEE.value}'>Flee</a> effect.",
            f"Despite being <a href='{GlossaryEntryType.ARMORED.value}'>{GlossaryEntryType.ARMORED.value}</a>, Black Knights are relatively fragile and can be overwhelmed before they can kill any units.",
            f"When facing Black Knights, you can often lure them into high damage units."
        ]
    },
    UnitType.CRUSADER_GOLD_KNIGHT: {
        "name": "Gold Knight",
        "description": f"<a href='{GlossaryEntryType.ARMORED.value}'>{GlossaryEntryType.ARMORED.value}</a> unit with <a href='{GlossaryEntryType.AREA_OF_EFFECT.value}'>{GlossaryEntryType.AREA_OF_EFFECT.value}</a> attack that heals per enemy hit.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CRUSADER_GOLD_KNIGHT_HP, armored=True, self_heal_dps=gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION * 1.5),
            StatType.SPEED: speed_stat(gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED),
            StatType.DAMAGE: damage_stat(gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION, 1.5),
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CRUSADER_GOLD_KNIGHT_HP} maximum health, armored. Heals {gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL} per enemy hit ({gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per enemy per second)",
            StatType.SPEED: f"{gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED} units per second",
            StatType.DAMAGE: f"{gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE} per hit, {gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE / gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION:.1f} per second",
        },
        "tips": [
            "Gold Knights are fast, <a href='{GlossaryEntryType.ARMORED.value}'>{GlossaryEntryType.ARMORED.value}</a> units that heal per enemy hit.",
            "Gold Knights are relatively fragile and can be overwhelmed before they can kill any units.",
            "When facing Gold Knights, you can often lure them into high damage units."
        ]
    },
    UnitType.CRUSADER_CLERIC: {
        "name": "Healer",
        "description": f"Support unit providing <a href='{GlossaryEntryType.HEALING.value}'>{GlossaryEntryType.HEALING.value}</a> to nearby allies.",
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
        "tips": [
            "Healers are support units that provide healing to nearby allies.",
            "Healers are relatively fragile and can be overwhelmed before they can heal any units.",
            "When facing Healers, you can often lure them into high damage units."
        ]
    },
    UnitType.ZOMBIE_BASIC_ZOMBIE: {
        "name": "Zombie",
        "description": f"Basic zombie that <a href='{GlossaryEntryType.INFECTION.value}'>{GlossaryEntryType.INFECTION.value}</a> enemies on hit.",
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
        "tips": [
            "Zombies are basic melee units that deal damage on hit.",
            "Zombies are relatively fragile and can be overwhelmed before they can kill any units.",
            "When facing Zombies, you can often lure them into high damage units."
        ]
    },
    UnitType.ZOMBIE_SPITTER: {
        "name": "Spitter",
        "description": f"Ranged zombie that <a href='{GlossaryEntryType.INFECTION.value}'>{GlossaryEntryType.INFECTION.value}</a> enemies from distance.",
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
        "tips": [
            "Spitters are ranged zombies that deal poison damage from a distance.",
            "Spitters are relatively fragile and can be overwhelmed before they can kill any units.",
            "When facing Spitters, you can often lure them into high damage units."
        ]
    },
    UnitType.ZOMBIE_TANK: {
        "name": "Tank",
        "description": f"Massive zombie with high health and <a href='{GlossaryEntryType.INFECTION.value}'>{GlossaryEntryType.INFECTION.value}</a>.",
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
        "tips": [
            "Tanks are massive melee units that deal damage on hit.",
            "Tanks are relatively fragile and can be overwhelmed before they can kill any units.",
            "When facing Tanks, you can often lure them into high damage units."
        ]
    },
    UnitType.CRUSADER_BANNER_BEARER: {
        "name": "Banner Bearer",
        "description": f"Support unit with <a href='{GlossaryEntryType.AURA.value}'>{GlossaryEntryType.AURA.value}</a> boosting defense and speed.",
        "stats": {
            StatType.DEFENSE: defense_stat(gc.CRUSADER_BANNER_BEARER_HP),
            StatType.SPEED: speed_stat(gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED),
            StatType.UTILITY: 10
        },
        "tooltips": {
            StatType.DEFENSE: f"{gc.CRUSADER_BANNER_BEARER_HP} maximum health",
            StatType.SPEED: f"{gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} units per second",
            StatType.UTILITY: f"+{int(gc.CRUSADER_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE * 100)}% damage, +{gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED} speed in {gc.CRUSADER_BANNER_BEARER_AURA_RADIUS} radius"
        },
        "tips": [
            "Banner Bearers are support units that boost defense and speed in a radius.",
            "Banner Bearers are relatively fragile and can be overwhelmed before they can boost any units.",
            "When facing Banner Bearers, you can often lure them into high damage units."
        ]
    },
} 