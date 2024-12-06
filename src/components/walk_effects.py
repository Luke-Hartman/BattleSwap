from typing import Dict, List
from effects import Effect


class WalkEffects:
    """Component for handling effects that occur when a unit walks."""

    def __init__(self, effects: Dict[int, List[Effect]]):
        self.effects = effects
