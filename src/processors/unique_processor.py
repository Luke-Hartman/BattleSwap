from collections import defaultdict
import esper

from components.unique import Unique

class UniqueProcessor:
    """Processor for unique components."""

    def process(self, dt: float):
        uniques_by_key = defaultdict(list)
        for ent, (unique,) in esper.get_components(Unique):
            unique.time_elapsed += dt
            uniques_by_key[unique.key].append((ent, unique))
        for uniques in uniques_by_key.values():
            new_unique = min(uniques, key=lambda x: x[1].time_elapsed)
            for ent, unique in uniques:
                if ent != new_unique[0]:
                    esper.delete_entity(ent)
