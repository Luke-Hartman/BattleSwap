"""Processor for units that are dying."""

import esper
from components.dying import Dying
from components.immunity import ImmuneToZombieInfection
from components.position import Position
from components.status_effect import StatusEffects, ZombieInfection
from components.unit_type import UnitType, UnitTypeComponent
from entities.units import create_unit
from events import DEATH, DeathEvent, emit_event
from voice import play_death

class DyingProcessor(esper.Processor):
    """Processor for units that are dying."""

    def process(self, dt: float):
        for ent, (dying, unit_type) in esper.get_components(Dying, UnitTypeComponent):
            emit_event(DEATH, event=DeathEvent(ent))
            play_death(unit_type.type)
            status_effects = esper.component_for_entity(ent, StatusEffects)
            position = esper.component_for_entity(ent, Position)
            if not esper.has_component(ent, ImmuneToZombieInfection):
                zombie_infection = next((effect for effect in status_effects.active_effects() if isinstance(effect, ZombieInfection)), None)
                if zombie_infection:
                    create_unit(
                        x=position.x,
                        y=position.y,
                        team=zombie_infection.team,
                        unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE
                    )
                    esper.delete_entity(ent)
            esper.remove_component(ent, Dying)
