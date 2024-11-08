"""Skill component."""

from dataclasses import dataclass

from components.aoe import AoEEffect
from visuals import Visual

class SkillEffect:
    """The effect of the skill."""

@dataclass
class SelfHeal(SkillEffect):
    """The effect of the skill."""

    percent: float
    """The percent of health to heal."""

@dataclass
class CreateAoE(SkillEffect):
    """The effect of the skill."""

    effect: AoEEffect
    """The AoE effect of the skill."""
    visual: Visual
    """The visual of the AoE."""
    duration: float
    """The duration of the AoE."""
    scale: float
    """The scale of the AoE."""

class TriggerCondition:
    """The condition that triggers the skill."""


@dataclass
class UnderHealthPercent(TriggerCondition):
    """The condition that triggers the skill on cooldown when the unit is low hp."""

    percent: float
    """The percent of health at which the skill is triggered."""

@dataclass
class TargetInRange(TriggerCondition):
    """The condition that triggers the skill when the target is in range."""

    range: float
    """The range of the skill."""

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
