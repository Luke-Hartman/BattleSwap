"""Component for tracking how long a unit has been dead."""

from dataclasses import dataclass


@dataclass
class CorpseTimer:
    """Tracks how long a unit has been dead."""
    time_dead: float = 0.0
