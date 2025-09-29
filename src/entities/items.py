"""Module for handling items in the game."""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict
import esper
import pygame
import os
from components.health import Health
from components.on_death_effects import OnDeathEffect
from components.on_hit_effects import OnHitEffects
from components.armor import Armor, ArmorLevel
from components.aura import Auras, Aura
from components.position import Position
from components.attached import Attached
from components.expiration import Expiration
from components.movement import Movement
from components.corruption import IncreasedMovementSpeedComponent
from components.team import Team
from unit_condition import All, Alive, Grounded, Always, HasComponent, NotHeavilyArmored
from effects import CreatesCircleAoE, CreatesVisual, Damages, PlaySound, Recipient, SoundEffect, Effect, AppliesStatusEffect, OnKillEffects, HealPercentageMax, CreatesAttachedVisual
from visuals import Visual
from components.status_effect import DamageOverTime, ZombieInfection
from game_constants import gc
from unit_condition import UnitCondition


class ExplodeOnDeathExplosionEffect(Effect):
    """Custom effect for ExplodeOnDeath explosion that can be identified and removed."""
    
    def __init__(self):
        self.effects = [
            CreatesCircleAoE(
                effects=[
                    Damages(damage=gc.ITEM_EXPLODE_ON_DEATH_DAMAGE, recipient=Recipient.TARGET),
                ],
                radius=gc.ITEM_EXPLODE_ON_DEATH_AOE_RADIUS,
                unit_condition=All([Alive(), Grounded()]),  # Hits both allies and enemies
                location=Recipient.PARENT,
            ),
            CreatesVisual(
                recipient=Recipient.PARENT,
                visual=Visual.Explosion,
                animation_duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,  # Same duration as wizard fireball
                scale=gc.ITEM_EXPLODE_ON_DEATH_AOE_RADIUS * gc.EXPLOSION_VISUAL_SCALE_RATIO,
                duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                layer=2,
            ),
            PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.50)),  # Same sound as wizard fireball
        ]
    
    def apply(self, owner: int, parent: int, target: int) -> None:
        """Apply all the explosion effects."""
        for effect in self.effects:
            effect.apply(owner, parent, target)


class ItemType(Enum):
    """Types of items that can be equipped to units."""
    EXTRA_HEALTH = "extra_health"
    EXPLODE_ON_DEATH = "EXPLODE_ON_DEATH"
    UPGRADE_ARMOR = "upgrade_armor"
    DAMAGE_AURA = "damage_aura"
    EXTRA_MOVEMENT_SPEED = "extra_movement_speed"
    HEAL_ON_KILL = "heal_on_kill"
    INFECT_ON_HIT = "infect_on_hit"

class Item(ABC):
    """Base class for all items."""
    
    @abstractmethod
    def apply(self, entity: int) -> None:
        """Apply the item's effect to the given entity."""
        pass
    
    @abstractmethod
    def remove(self, entity: int) -> None:
        """Remove the item's effect from the given entity."""
        pass
    
    @classmethod
    @abstractmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition that determines which units this item can be applied to."""
        pass

class ExtraHealth(Item):
    """Grants extra HP to the equipped unit."""

    def apply(self, entity: int) -> None:
        """Apply health bonus to the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current += gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
            health.maximum += gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
    
    def remove(self, entity: int) -> None:
        """Remove health bonus from the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current -= gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
            health.maximum -= gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class ExplodeOnDeath(Item):
    """An item that creates an explosion when the unit dies, damaging all nearby units."""
    
    def apply(self, entity: int) -> None:
        """Add death explosion effect to the entity."""
        death_effect = esper.component_for_entity(entity, OnDeathEffect)
        death_effect.effects.append(ExplodeOnDeathExplosionEffect())
    
    def remove(self, entity: int) -> None:
        """Remove the death explosion effect from the entity."""
        death_effect = esper.component_for_entity(entity, OnDeathEffect)
        for effect in death_effect.effects:
            if isinstance(effect, ExplodeOnDeathExplosionEffect):
                death_effect.effects.remove(effect)
                break
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class UpgradeArmor(Item):
    """Upgrades a unit's armor. If no armor, adds normal armor. If normal armor, upgrades to heavily armored."""
    
    def apply(self, entity: int) -> None:
        """Apply armor upgrade to the entity."""
        if not esper.has_component(entity, Armor):
            # No armor - add normal armor
            esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
        else:
            # Has armor - upgrade to heavily armored
            armor = esper.component_for_entity(entity, Armor)
            armor.level = ArmorLevel.HEAVILY
    
    def remove(self, entity: int) -> None:
        """Remove armor upgrade from the entity."""
        if esper.has_component(entity, Armor):
            armor = esper.component_for_entity(entity, Armor)
            if armor.level == ArmorLevel.HEAVILY:
                # Downgrade to normal armor
                armor.level = ArmorLevel.NORMAL
            else:
                # Remove armor completely
                esper.remove_component(entity, Armor)
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item - can only be applied to units that are not heavily armored."""
        return NotHeavilyArmored()


class DamageAura(Item):
    """Grants the unit a red aura that deals damage to all units in range, including itself."""
    
    def apply(self, entity: int) -> None:
        """Apply damage aura to the entity."""
        # Get or create the Auras component
        if esper.has_component(entity, Auras):
            auras = esper.component_for_entity(entity, Auras)
        else:
            auras = Auras()
            esper.add_component(entity, auras)
        
        # Create and add the damage aura
        damage_aura = Aura(
            owner=entity,
            radius=gc.ITEM_DAMAGE_AURA_RADIUS,
            effects=[
                AppliesStatusEffect(
                    status_effect=DamageOverTime(dps=gc.ITEM_DAMAGE_AURA_DAMAGE_PER_SECOND, time_remaining=gc.DEFAULT_AURA_PERIOD, owner=entity),
                    recipient=Recipient.TARGET
                )
            ],
            color=(255, 0, 0),  # Red color
            period=gc.DEFAULT_AURA_PERIOD,
            owner_condition=Alive(),
            unit_condition=Alive(),
            duration=float('inf')  # Permanent
        )
        # Add a marker to identify this as a damage aura
        damage_aura._aura_type = DamageAura
        auras.auras.append(damage_aura)
    
    def remove(self, entity: int) -> None:
        """Remove damage aura from the entity."""
        if esper.has_component(entity, Auras):
            auras = esper.component_for_entity(entity, Auras)
            # Remove the first damage aura found
            for aura in auras.auras:
                if hasattr(aura, '_aura_type') and aura._aura_type == DamageAura:
                    auras.auras.remove(aura)
                    break
            # If no more auras, remove the Auras component
            if not auras.auras:
                esper.remove_component(entity, Auras)
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class ExtraMovementSpeed(Item):
    """Grants extra movement speed to the equipped unit."""
    
    def apply(self, entity: int) -> None:
        """Apply movement speed bonus to the entity."""
        movement = esper.component_for_entity(entity, Movement)
        movement.speed += gc.ITEM_EXTRA_MOVEMENT_SPEED_BONUS
    
    def remove(self, entity: int) -> None:
        """Remove movement speed bonus from the entity."""
        movement = esper.component_for_entity(entity, Movement)
        movement.speed -= gc.ITEM_EXTRA_MOVEMENT_SPEED_BONUS
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return HasComponent(Movement)


class InfectOnHit(Item):
    """Grants zombie infection on hit."""
    
    def apply(self, entity: int) -> None:
        """Apply infect on hit effect to the entity."""
        # Add OnHitEffects component for zombie infection on hit
        esper.add_component(
            entity,
            OnHitEffects(
                effects=[
                    AppliesStatusEffect(
                        status_effect=ZombieInfection(
                            time_remaining=gc.ZOMBIE_INFECTION_DURATION, 
                            team=esper.component_for_entity(entity, Team).type,
                            corruption_powers=None, 
                            owner=entity
                        ),
                        recipient=Recipient.TARGET
                    )
                ]
            )
        )
    
    def remove(self, entity: int) -> None:
        """Remove infect on hit effect from the entity."""
        if esper.has_component(entity, OnHitEffects):
            esper.remove_component(entity, OnHitEffects)
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class HealOnKill(Item):
    """Grants healing for half of maximum health when the unit gets a kill."""
    
    def apply(self, entity: int) -> None:
        """Apply heal on kill effect to the entity."""
        # Add OnKillEffects component for healing on kill
        esper.add_component(
            entity,
            OnKillEffects(
                effects=[
                    HealPercentageMax(
                        recipient=Recipient.OWNER,
                        percentage=0.5,
                        duration=1.0
                    ),
                    PlaySound([
                        (SoundEffect(filename=f"heal.wav", volume=0.50), 1.0)
                    ]),
                    CreatesAttachedVisual(
                        recipient=Recipient.OWNER,
                        visual=Visual.Healing,
                        animation_duration=1,
                        expiration_duration=1,
                        scale=2,
                        random_starting_frame=True,
                        layer=1,
                        on_death=lambda e: esper.delete_entity(e),
                    )
                ]
            )
        )
    
    def remove(self, entity: int) -> None:
        """Remove heal on kill effect from the entity."""
        if esper.has_component(entity, OnKillEffects):
            esper.remove_component(entity, OnKillEffects)
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


# Item theme IDs for UI styling
item_theme_ids: Dict[ItemType, str] = {
    ItemType.EXTRA_HEALTH: "#extra_health_icon",
    ItemType.EXPLODE_ON_DEATH: "#explode_on_death_icon",
    ItemType.UPGRADE_ARMOR: "#upgrade_armor_icon",
    ItemType.DAMAGE_AURA: "#damage_aura_icon",
    ItemType.EXTRA_MOVEMENT_SPEED: "#extra_movement_speed_icon",
    ItemType.HEAL_ON_KILL: "#heal_on_kill_icon",
    ItemType.INFECT_ON_HIT: "#infect_on_hit_icon"
}

# Item icon surfaces for rendering
item_icon_surfaces: Dict[ItemType, pygame.Surface] = {}

# Item registry
item_registry: Dict[ItemType, Item] = {
    ItemType.EXTRA_HEALTH: ExtraHealth(),
    ItemType.EXPLODE_ON_DEATH: ExplodeOnDeath(),
    ItemType.UPGRADE_ARMOR: UpgradeArmor(),
    ItemType.DAMAGE_AURA: DamageAura(),
    ItemType.EXTRA_MOVEMENT_SPEED: ExtraMovementSpeed(),
    ItemType.HEAL_ON_KILL: HealOnKill(),
    ItemType.INFECT_ON_HIT: InfectOnHit()
}


def load_item_icons() -> None:
    """Load all item icons."""
    item_icon_paths: Dict[ItemType, str] = {
        ItemType.EXTRA_HEALTH: "ExtraHealthIcon.png",
        ItemType.EXPLODE_ON_DEATH: "ExplodeOnDeathIcon.png",
        ItemType.UPGRADE_ARMOR: "UpgradeArmorIcon.png",
        ItemType.DAMAGE_AURA: "DamageAuraIcon.png",
        ItemType.EXTRA_MOVEMENT_SPEED: "ExtraMovementSpeedIcon.png",
        ItemType.HEAL_ON_KILL: "HealOnKillIcon.png",
        ItemType.INFECT_ON_HIT: "InfectOnHitIcon.png",
    }
    
    for item_type, filename in item_icon_paths.items():
        if item_type in item_icon_surfaces:
            continue
        path = os.path.join("assets", "icons", filename)
        item_icon_surfaces[item_type] = pygame.image.load(path).convert_alpha()