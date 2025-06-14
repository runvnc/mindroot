import json
import os

class DataAccess:
    def __init__(self):
        self.data_dir = 'data'
        self.models_file = os.path.join(self.data_dir, 'models.json')
        self.providers_file = os.path.join(self.data_dir, 'providers.json')
        self.plugins_file = 'data/plugin_manifest.json'
        self.equivalent_flags_file = os.path.join(self.data_dir, 'equivalent_flags.json')
        self.preferred_models_file = os.path.join(self.data_dir, 'preferred_models.json')

    def read_json(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def write_json(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    # Models
    def read_models(self):
        return self.read_json(self.models_file)

    def write_models(self, models):
        self.write_json(self.models_file, models)

    def get_model(self, model_name):
        models = self.read_models()
        return next((model for model in models if model['name'] == model_name), None)

    def update_model(self, model_name, updates):
        models = self.read_models()
        for model in models:
            if model['name'] == model_name:
                model.update(updates)
                break
        self.write_models(models)

    # Providers
    def read_providers(self):
        return self.read_json(self.providers_file)

    def write_providers(self, providers):
        self.write_json(self.providers_file, providers)

    def get_provider(self, provider_name):
        providers = self.read_providers()
        return next((provider for provider in providers if provider['name'] == provider_name), None)

    def add_provider(self, provider_data):
        providers = self.read_providers()
        providers.append(provider_data)
        self.write_providers(providers)

    def remove_provider(self, provider_name):
        providers = self.read_providers()
        providers = [p for p in providers if p['name'] != provider_name]
        self.write_providers(providers)

    def update_provider(self, provider_name, updates):
        providers = self.read_providers()
        for provider in providers:
            if provider['name'] == provider_name:
                provider.update(updates)
                break
        self.write_providers(providers)

    # Plugins
    def read_plugins(self):
        try:
            manifest = self.read_json(self.plugins_file)
            all_plugins = []
            for category in ['core', 'local', 'installed']:
                for plugin_name, plugin_info in manifest['plugins'].get(category, {}).items():
                    all_plugins.append({
                        'name': plugin_name,
                        'enabled': plugin_info.get('enabled', False),
                        'category': category,
                        **plugin_info
                    })
            return all_plugins
        except FileNotFoundError:
            print(f"Warning: {self.plugins_file} not found. Returning empty list.")
            return []
        except json.JSONDecodeError:
            print(f"Error: {self.plugins_file} is not a valid JSON file. Returning empty list.")
            return []
        except KeyError:
            print(f"Error: {self.plugins_file} does not have the expected structure. Returning empty list.")
            return []

    def write_plugins(self, plugins):
        manifest = {'plugins': {'core': {}, 'local': {}, 'installed': {}}}
        for plugin in plugins:
            category = plugin.pop('category', 'installed')
            name = plugin.pop('name')
            manifest['plugins'][category][name] = plugin
        self.write_json(self.plugins_file, manifest)

    def add_plugin(self, plugin_data):
        manifest = self.read_json(self.plugins_file)
        category = plugin_data.get('category', 'installed')
        name = plugin_data['name']
        manifest['plugins'][category][name] = plugin_data
        self.write_json(self.plugins_file, manifest)

    def remove_plugin(self, plugin_name):
        manifest = self.read_json(self.plugins_file)
        for category in manifest['plugins']:
            if plugin_name in manifest['plugins'][category]:
                del manifest['plugins'][category][plugin_name]
                self.write_json(self.plugins_file, manifest)
                return

    def update_plugin(self, plugin_name, updates):
        manifest = self.read_json(self.plugins_file)
        for category in manifest['plugins']:
            if plugin_name in manifest['plugins'][category]:
                manifest['plugins'][category][plugin_name].update(updates)
                self.write_json(self.plugins_file, manifest)
                return

    # Equivalent Flags
    def read_equivalent_flags(self):
        return self.read_json(self.equivalent_flags_file)

    def write_equivalent_flags(self, flags):
        self.write_json(self.equivalent_flags_file, flags)

    # Preferred Models
    def read_preferred_models(self):
        if not os.path.exists(self.preferred_models_file):
            self.write_json(self.preferred_models_file, [])
        return self.read_json(self.preferred_models_file)

    def write_preferred_models(self, models):
        self.write_json(self.preferred_models_file, models)
