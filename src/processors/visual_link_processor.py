import esper
from components.visual_link import VisualLink

class VisualLinkProcessor(esper.Processor):
    def process(self, dt: float):
        for ent, (visual_link,) in esper.get_components(VisualLink):
            if visual_link.entity_delete_condition and visual_link.entity_delete_condition.check(ent):
                esper.remove_component(ent, VisualLink)
            if visual_link.other_entity_delete_condition and visual_link.other_entity_delete_condition.check(ent):
                esper.remove_component(ent, VisualLink)