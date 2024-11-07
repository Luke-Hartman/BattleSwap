"""Processor for aura effects."""

import esper
from components.aura import Aura, AffectedByAuras
from components.position import Position
from components.team import Team


class AuraProcessor(esper.Processor):
    """Processor for aura effects."""

    def process(self, dt: float):
        for other_ent, (affected_by_auras, other_position, other_team) in esper.get_components(AffectedByAuras, Position, Team):
            affected_by_auras.clear()
        for ent, (aura, position, team) in esper.get_components(Aura, Position, Team):
            for other_ent, (affected_by_auras, other_position, other_team) in esper.get_components(AffectedByAuras, Position, Team):
                if ent == other_ent:
                    affected_by_auras.add(aura.effect)
                elif (other_position.x - position.x)**2 + (other_position.y - position.y)**2 <= aura.radius**2:
                    if team.type == other_team.type and aura.effect.affects_allies:
                        affected_by_auras.add(aura.effect)
                    elif team.type != other_team.type and aura.effect.affects_enemies:
                        affected_by_auras.add(aura.effect)
