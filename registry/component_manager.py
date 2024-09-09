class ComponentManager:
    def __init__(self):
        self.components = {}

    def register_component(self, component_type, name, metadata):
        if component_type not in self.components:
            self.components[component_type] = {}
        self.components[component_type][name] = metadata

    def is_component_installed(self, component_type, name):
        return component_type in self.components and name in self.components[component_type]

    def is_component_activated(self, component_type, name):
        if self.is_component_installed(component_type, name):
            return self.components[component_type][name].get('activated', False)
        return False

    def list_components(self, component_type):
        return list(self.components.get(component_type, {}).keys())

    def get_component_metadata(self, component_type, name):
        if self.is_component_installed(component_type, name):
            return self.components[component_type][name]
        return None
