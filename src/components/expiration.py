"""Component for entities that expire after a certain amount of time."""

from dataclasses import dataclass

@dataclass
class Expiration:
    """Component for entities that expire after a certain amount of time."""
    time_left: float
