"""Processor for expiring entities."""

import esper

from components.expiration import Expiration


class ExpirationProcessor(esper.Processor):
    """Processor for expiring entities."""

    def process(self, dt: float):
        for entity, expiration in esper.get_component(Expiration):
            expiration.time_left -= dt
            if expiration.time_left <= 0:
                esper.delete_entity(entity)
