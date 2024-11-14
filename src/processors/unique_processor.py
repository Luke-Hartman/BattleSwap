from collections import defaultdict
import esper

from components.unique import Unique

class UniqueProcessor:
    """Processor for unique components."""

    def process(self, dt: float):
        uniques_by_key = defaultdict(list)
        for ent, (unique,) in esper.get_components(Unique):
            uniques_by_key[unique.key].append((ent, unique))
        for uniques in uniques_by_key.values():
            oldest_unique = min(uniques, key=lambda x: x[1].created_at)
            for ent, unique in uniques:
                if ent != oldest_unique[0]:
                    esper.delete_entity(ent, immediate=True)
