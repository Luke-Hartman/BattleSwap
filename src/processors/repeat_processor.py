"""Processor for repeat components."""

import esper
from components.repeat import Repeat

class RepeatProcessor(esper.Processor):
    """Processor for repeat components that continually apply effects at intervals."""
    
    def process(self, dt: float):
        for ent, (repeat,) in esper.get_components(Repeat):
            # Check if the stop condition is met
            if repeat.stop_condition.check(ent):
                esper.remove_component(ent, Repeat)
                continue
            
            # Update the time since creation
            repeat.time_since_creation += dt
            
            # Check if it's time to apply effects using modulo
            # This ensures effects are applied at consistent intervals
            if repeat.time_since_creation % repeat.interval < dt:
                # Apply all effects
                for effect in repeat.effects:
                    effect.apply(
                        owner=repeat.owner,
                        parent=repeat.parent,
                        target=repeat.target
                    )
