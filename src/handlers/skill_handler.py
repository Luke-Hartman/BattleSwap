"""Skill handler module for Battle Swap.

This module contains the SkillHandler class, which is responsible for
handling skill logic.
"""

import esper
from components.health import Health
from components.skill import SelfHeal, Skill
from events import SkillActivatedEvent, SKILL_ACTIVATED
from pydispatch import dispatcher

class SkillHandler:
    """Handler responsible for handling skill logic."""

    def __init__(self):
        dispatcher.connect(self.handle_skill_activated, signal=SKILL_ACTIVATED)

    def handle_skill_activated(self, event: SkillActivatedEvent):
        entity = event.entity
        skill = esper.component_for_entity(entity, Skill)
        if isinstance(skill.effect, SelfHeal):
            health = esper.component_for_entity(entity, Health)
            health.current = min(health.current + skill.effect.percent * health.maximum, health.maximum)
        else:
            raise ValueError(f"Skill effect {skill.effect} not supported")
