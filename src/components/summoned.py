"""Component for tracking entities created by a specific summoner.

This component is attached to units that were created by another entity's
ability (e.g., necromancer summons). It allows systems to identify and
manipulate only those summons belonging to a particular summoner.
"""

from dataclasses import dataclass


@dataclass
class SummonedBy:
    """Marks an entity as having been summoned by a specific summoner entity."""

    summoner: int
    """Entity id of the summoner that created this unit."""


