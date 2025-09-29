"""Component for units that are dying.

This is just to allow units to finish their current frame before dying.

This allows mirroring units to both kill each other at the same time.
"""

from dataclasses import dataclass


@dataclass
class Dying:
    """Component for units that are dying."""
