from typing import Dict, List
from effects import Effect
from components.animation import AnimationType

class AnimationEffects:
    """Component for handling effects that occur when a unit reaches a certain animation frame."""

    def __init__(self, effects: Dict[AnimationType, Dict[int, List[Effect]]]):
        self.effects = effects
