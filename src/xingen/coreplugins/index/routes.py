import os
import json
from pathlib import Path
from flask import jsonify, request, current_app

# Define the directory where index files will be stored
INDEX_DIR = Path(current_app.instance_path) / 'indices' if 'current_app' in locals() else Path('./indices')

def init_routes(app):
    # Ensure index directory exists
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    @app.route('/index/list-indices')
    def list_indices():
        """List all available indices"""
        try:
            indices = []
            for file in INDEX_DIR.glob('*.json'):
                with open(file, 'r') as f:
                    index_data = json.load(f)
                    indices.append(index_data)
            return jsonify({'success': True, 'data': indices})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/index/create-index', methods=['POST'])
    def create_index():
        """Create a new index"""
        try:
            data = request.json
            name = data.get('name')
            if not name:
                return jsonify({'success': False, 'message': 'Name is required'})

            # Create index file
            file_path = INDEX_DIR / f"{name}.json"
            if file_path.exists():
                return jsonify({'success': False, 'message': 'Index already exists'})

            index_data = {
                'name': name,
                'description': data.get('description', ''),
                'version': data.get('version', '1.0.0'),
                'plugins': [],
                'agents': []
            }

            with open(file_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            return jsonify({'success': True, 'data': index_data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/index/update-index', methods=['POST'])
    def update_index():
        """Update index metadata"""
        try:
            data = request.json
            name = data.get('name')
            if not name:
                return jsonify({'success': False, 'message': 'Name is required'})

            file_path = INDEX_DIR / f"{name}.json"
            if not file_path.exists():
                return jsonify({'success': False, 'message': 'Index not found'})

            with open(file_path, 'r') as f:
                index_data = json.load(f)

            # Update fields
            for field in ['name', 'description', 'version']:
                if field in data:
                    index_data[field] = data[field]

            with open(file_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            return jsonify({'success': True, 'data': index_data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/index/add-plugin', methods=['POST'])
    def add_plugin():
        """Add a plugin to an index"""
        try:
            data = request.json
            index_name = data.get('index')
            plugin_name = data.get('plugin')

            if not index_name or not plugin_name:
                return jsonify({'success': False, 'message': 'Index and plugin names are required'})

            file_path = INDEX_DIR / f"{index_name}.json"
            if not file_path.exists():
                return jsonify({'success': False, 'message': 'Index not found'})

            # Load plugin manifest to get plugin details
            manifest_path = Path(app.root_path) / 'plugin_manifest.json'
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Find plugin in manifest
            plugin_data = None
            for category in ['core', 'installed', 'available']:
                if plugin_name in manifest['plugins'].get(category, {}):
                    plugin_data = manifest['plugins'][category][plugin_name]
                    plugin_data['name'] = plugin_name
                    break

            if not plugin_data:
                return jsonify({'success': False, 'message': 'Plugin not found in manifest'})

            # Add to index
            with open(file_path, 'r') as f:
                index_data = json.load(f)

            # Check if plugin already exists
            if any(p['name'] == plugin_name for p in index_data['plugins']):
                return jsonify({'success': False, 'message': 'Plugin already in index'})

            index_data['plugins'].append(plugin_data)

            with open(file_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            return jsonify({'success': True, 'data': index_data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/index/add-agent', methods=['POST'])
    def add_agent():
        """Add an agent to an index"""
        try:
            data = request.json
            index_name = data.get('index')
            agent_name = data.get('agent')

            if not index_name or not agent_name:
                return jsonify({'success': False, 'message': 'Index and agent names are required'})

            file_path = INDEX_DIR / f"{index_name}.json"
            if not file_path.exists():
                return jsonify({'success': False, 'message': 'Index not found'})

            # TODO: Load agent details from appropriate source
            agent_data = {
                'name': agent_name,
                'version': '1.0.0',
                # Add other agent metadata as needed
            }

            with open(file_path, 'r') as f:
                index_data = json.load(f)

            # Check if agent already exists
            if any(a['name'] == agent_name for a in index_data['agents']):
                return jsonify({'success': False, 'message': 'Agent already in index'})

            index_data['agents'].append(agent_data)

            with open(file_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            return jsonify({'success': True, 'data': index_data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/index/remove-plugin', methods=['POST'])
    def remove_plugin():
        """Remove a plugin from an index"""
        try:
            data = request.json
            index_name = data.get('index')
            plugin_name = data.get('plugin')

            if not index_name or not plugin_name:
                return jsonify({'success': False, 'message': 'Index and plugin names are required'})

            file_path = INDEX_DIR / f"{index_name}.json"
            if not file_path.exists():
                return jsonify({'success': False, 'message': 'Index not found'})

            with open(file_path, 'r') as f:
                index_data = json.load(f)

            index_data['plugins'] = [p for p in index_data['plugins'] if p['name'] != plugin_name]

            with open(file_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            return jsonify({'success': True, 'data': index_data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/index/remove-agent', methods=['POST'])
    def remove_agent():
        """Remove an agent from an index"""
        try:
            data = request.json
            index_name = data.get('index')
            agent_name = data.get('agent')

            if not index_name or not agent_name:
                return jsonify({'success': False, 'message': 'Index and agent names are required'})

            file_path = INDEX_DIR / f"{index_name}.json"
            if not file_path.exists():
                return jsonify({'success': False, 'message': 'Index not found'})

            with open(file_path, 'r') as f:
                index_data = json.load(f)

            index_data['agents'] = [a for a in index_data['agents'] if a['name'] != agent_name]

            with open(file_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            return jsonify({'success': True, 'data': index_data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
