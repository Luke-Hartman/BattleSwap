from dataclasses import dataclass

@dataclass
class ForcedMovement:
    """Component for forced movement."""

    destination_x: int
    """The x destination of the forced movement."""

    destination_y: int
    """The y destination of the forced movement."""

    speed: float
    """The speed of the forced movement."""