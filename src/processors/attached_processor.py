"""Processor for attached entities."""

import esper
from components.attached import Attached
from components.position import Position
from components.unit_state import State, UnitState

class AttachedProcessor(esper.Processor):
    """Processor for attached entities."""

    def process(self, dt: float):
        for ent, (attached, pos) in esper.get_components(Attached, Position):
            # If entity that is attached to this entity is deleted, delete this entity
            if not esper.has_component(attached.entity, Position):
                esper.delete_entity(ent)
            elif attached.on_death is not None and esper.component_for_entity(attached.entity, UnitState).state == State.DEAD:
                attached.on_death(ent)
            else:
                attached_position = esper.component_for_entity(attached.entity, Position)
                pos.x = attached_position.x + attached.offset[0]
                pos.y = attached_position.y + attached.offset[1]
