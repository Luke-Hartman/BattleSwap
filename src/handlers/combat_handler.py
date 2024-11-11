"""Combat handler module for Battle Swap.

This module contains the CombatHandler class, which is responsible for
handling attack/skill/AoE/etc logic and applying damage/healing from attacks/skills/AoEs/etc.
"""

import esper
from components.ability import Abilities
from components.aoe import AoE
from components.aura import Aura
from components.projectile import Projectile
from components.unit_state import UnitState
from components.team import Team
from events import (
    AbilityActivatedEvent, ABILITY_ACTIVATED,
    AoEHitEvent, AOE_HIT,
    AuraHitEvent, AURA_HIT,
    ProjectileHitEvent, PROJECTILE_HIT,
)
from pydispatch import dispatcher

class CombatHandler:
    """Handler responsible for handling attack logic and applying damage."""

    def __init__(self):
        dispatcher.connect(self.handle_ability_activated, signal=ABILITY_ACTIVATED)
        dispatcher.connect(self.handle_projectile_hit, signal=PROJECTILE_HIT)
        dispatcher.connect(self.handle_aoe_hit, signal=AOE_HIT)
        dispatcher.connect(self.handle_aura_hit, signal=AURA_HIT)

    def handle_ability_activated(self, event: AbilityActivatedEvent):
        owner = event.entity
        abilities = esper.component_for_entity(owner, Abilities)
        ability = abilities.abilities[event.index]
        for effect in ability.effects[event.frame]:
            effect.apply(
                owner=owner,
                parent=owner,
                target=ability.target
            )

    def handle_projectile_hit(self, event: ProjectileHitEvent):
        projectile_ent = event.entity
        target_ent = event.target
        projectile = esper.component_for_entity(projectile_ent, Projectile)
        for effect in projectile.effects:
            effect.apply(
                owner=projectile.owner,
                parent=projectile_ent,
                target=target_ent
            )

    def handle_aoe_hit(self, event: AoEHitEvent):
        aoe_ent = event.entity
        target_ent = event.target
        aoe = esper.component_for_entity(aoe_ent, AoE)
        if target_ent in aoe.hit_entities:
            return
        aoe.hit_entities.append(target_ent)
        aoe_team = esper.component_for_entity(aoe_ent, Team)
        target_team = esper.component_for_entity(target_ent, Team)
        is_owner = target_ent == aoe.owner
        is_ally = aoe_team.type == target_team.type and not is_owner
        is_enemy = aoe_team.type != target_team.type
        if (
            aoe.hits_allies and is_ally or
            aoe.hits_enemies and is_enemy or
            aoe.hits_owner and is_owner
        ):
            for effect in aoe.effects:
                effect.apply(
                    owner=aoe.owner,
                    parent=aoe_ent,
                    target=target_ent
                )

    def handle_aura_hit(self, event: AuraHitEvent):
        owner_ent = event.entity
        target_ent = event.target
        aura = esper.component_for_entity(owner_ent, Aura)
        aura_team = esper.component_for_entity(owner_ent, Team)
        target_team = esper.component_for_entity(target_ent, Team)
        ally = aura_team.type == target_team.type
        if (
            aura.hits_allies and ally or
            aura.hits_enemies and not ally or
            aura.hits_owner and target_ent == aura.owner
        ):
            for effect in aura.effects:
                effect.apply(
                    owner=owner_ent,
                    parent=owner_ent,
                    target=target_ent
                )

