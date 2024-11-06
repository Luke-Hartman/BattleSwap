"""Processor for skills with cooldowns."""

import time
import esper
from components.health import Health
from components.skill import Skill, UnderHealthPercent
from components.unit_state import State, UnitState
from events import SKILL_TRIGGERED, SkillTriggeredEvent, emit_event

class CooldownSkillProcessor(esper.Processor):
    """Processor for skills with cooldowns."""

    def process(self, dt: float):
        for ent, (skill, unit_state) in esper.get_components(Skill, UnitState):
            if unit_state.state == State.DEAD:
                continue
            if not skill.last_used + skill.cooldown < time.time():
                continue
            if isinstance(skill.trigger_condition, UnderHealthPercent):
                health = esper.component_for_entity(ent, Health)
                if health.current / health.maximum <= skill.trigger_condition.percent:
                    skill.last_used = time.time()
                    emit_event(SKILL_TRIGGERED, event=SkillTriggeredEvent(ent))
