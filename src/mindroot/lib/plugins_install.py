import json
import subprocess
import sys
from pathlib import Path

def install_plugins(plugin_list):
    try:
        poetry_cmd = [sys.executable, '-m', 'poetry', 'add']
        for plugin in plugin_list:
            poetry_cmd.append(f"{plugin['name']}@{plugin['version']}")
        result = subprocess.run(poetry_cmd, check=True, capture_output=True, text=True)
        return (True, plugin_list)
    except subprocess.CalledProcessError as e:
        return (False, [])

def update_plugins_json(installed_plugins, json_path):
    try:
        with open(json_path, 'r') as f:
            existing_plugins = json.load(f)
    except FileNotFoundError:
        existing_plugins = []
    for new_plugin in installed_plugins:
        existing = next((p for p in existing_plugins if p['name'] == new_plugin['name']), None)
        if existing:
            existing['version'] = new_plugin['version']
        else:
            existing_plugins.append({'name': new_plugin['name'], 'version': new_plugin['version'], 'enabled': False})
    with open(json_path, 'w') as f:
        json.dump(existing_plugins, f, indent=2)

def main():
    json_path = Path('/files/ah/plugins.json')
    plugins_to_install = [{'name': 'requests', 'version': '2.26.0'}, {'name': 'beautifulsoup4', 'version': '4.9.3'}]
    success, installed_plugins = install_plugins(plugins_to_install)
    if success:
        update_plugins_json(installed_plugins, json_path)
if __name__ == '__main__':
    main()