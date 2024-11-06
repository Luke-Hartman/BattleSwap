"""Skill component."""

from dataclasses import dataclass

class SkillEffect:
    """The effect of the skill."""


@dataclass
class SelfHeal(SkillEffect):
    """The effect of the skill."""

    percent: float
    """The percent of health to heal."""


class TriggerCondition:
    """The condition that triggers the skill."""


@dataclass
class UnderHealthPercent(TriggerCondition):
    """The condition that triggers the skill on cooldown when the unit is low hp."""

    percent: float
    """The percent of health at which the skill is triggered."""


@dataclass
class Skill:
    """Component representing a unit's skill."""

    trigger_condition: TriggerCondition
    """The condition that triggers the skill."""

    effect: SkillEffect
    """The effect of the skill."""

    cooldown: float
    """The cooldown of the skill, in seconds."""

    last_used: float = -float("inf")
    """The time at which the skill was last used."""