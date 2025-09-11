"""Processor responsible for targetting."""


from collections import defaultdict
import esper
from components.ability import Abilities
from components.destination import Destination
from components.instant_ability import InstantAbilities
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.status_effect import Invisible, StatusEffects
from components.unusable_corpse import UnusableCorpse
from target_strategy import TargetingGroup
from components.sprite_sheet import SpriteSheet


class TargettingProcessor(esper.Processor):
    """Processor responsible for targetting."""

    def process(self, dt: float):
        targetting_groups = defaultdict(set)

        for ent, (unit_state, team) in esper.get_components(UnitState, Team):
            # Check if unit is invisible
            is_invisible = False
            if esper.has_component(ent, StatusEffects):
                status_effects = esper.component_for_entity(ent, StatusEffects)
                is_invisible = any(
                    isinstance(effect, Invisible)
                    for effect in status_effects.active_effects()
                )
            if is_invisible:
                continue

            if unit_state.state == State.DEAD:
                # This is a hack which means the corpse should be deleted.
                if not esper.has_component(ent, SpriteSheet):
                    continue
                if not esper.has_component(ent, UnusableCorpse):
                    targetting_groups[TargetingGroup.USABLE_CORPSES].add(ent)
            elif team.type == TeamType.TEAM1:
                targetting_groups[TargetingGroup.TEAM1_LIVING_VISIBLE].add(ent)
            else:
                targetting_groups[TargetingGroup.TEAM2_LIVING_VISIBLE].add(ent)

        target_strategies = set()
        for ent, (unit_state, destination) in esper.get_components(UnitState, Destination):
            target_strategies.add((ent, unit_state.state, destination.target_strategy))
        for ent, (unit_state, instant_abilities) in esper.get_components(UnitState, InstantAbilities):
            for ability in instant_abilities.abilities:
                target_strategies.add((ent, unit_state.state, ability.target_strategy))
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            for ability in abilities.abilities:
                target_strategies.add((ent, unit_state.state, ability.target_strategy))
        for ent, state, target_strategy in target_strategies:
            # Consider new targets
            if state == State.IDLE or state == State.PURSUING:
                target_strategy.find_target(targetting_groups)
            elif state == State.DEAD:
                target_strategy.target = None
