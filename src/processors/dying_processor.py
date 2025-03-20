"""Processor for units that are dying."""

import esper
from components.dying import Dying, OnDeathEffect
from components.position import Position
from components.unit_type import UnitType, UnitTypeComponent
from components.transparent import Transparency
from entities.units import create_unit
from events import DEATH, DeathEvent, emit_event
from unit_condition import Infected
from voice import play_death

class DyingProcessor(esper.Processor):
    """Processor for units that are dying."""

    def process(self, dt: float):
        for ent, (_, unit_type) in esper.get_components(Dying, UnitTypeComponent):
            emit_event(DEATH, event=DeathEvent(ent))
            play_death(unit_type.type)
            
            # Handle on death effects
            if esper.has_component(ent, OnDeathEffect):
                on_death = esper.component_for_entity(ent, OnDeathEffect)
                if on_death.condition is None or on_death.condition.check(ent):
                    for effect in on_death.effects:
                        effect.apply(owner=ent, parent=ent, target=None)

            # Handle zombie infection
            team = Infected().check_return_team(ent)
            if team:
                position = esper.component_for_entity(ent, Position)
                create_unit(
                    x=position.x,
                    y=position.y,
                    team=team,
                    unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE
                )
                esper.add_component(ent, Transparency(alpha=0))
            
            esper.remove_component(ent, Dying)
