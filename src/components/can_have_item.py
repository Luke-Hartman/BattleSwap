"""Component for marking units that can have items placed on them."""

from dataclasses import dataclass


@dataclass
class CanHaveItem:
    """Component that marks a unit as being able to have items placed on it.
    
    This is used during item placement mode to show visual indicators
    around units that can receive items.
    """
    pass
