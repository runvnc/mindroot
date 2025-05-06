import os
import sys
import json
import shutil
import tempfile
import requests
import zipfile
import subprocess
from pkg_resources import require as pkg_require
from .manifest import update_plugin_manifest
import traceback

def download_github_files(repo_path, tag=None):
    """Download GitHub repo files to temp directory.
    
    Args:
        repo_path (str): GitHub repository path (user/repo)
        tag (str, optional): Specific tag to download
        
    Returns:
        tuple: (plugin_dir, plugin_root, plugin_info)
    """
    download_url = f"https://github.com/{repo_path}/archive/refs/tags/{tag}.zip" if tag else \
                  f"https://github.com/{repo_path}/archive/refs/heads/main.zip"
    
    repo = repo_path.split("/")[1]
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'repo.zip')

    print(f"Github install: Downloading {download_url} to {zip_path}")
    try:
        response = requests.get(download_url)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        os.remove(zip_path)
            
        # Find plugin_info.json
        for root, _, files in os.walk(temp_dir):
            if 'plugin_info.json' in files:
                with open(os.path.join(root, 'plugin_info.json'), 'r') as f:
                    plugin_info = json.load(f)
                
                # Setup local plugin directory
                if os.path.exists(f"./local/plugins/{repo}"):
                    shutil.rmtree(f"./local/plugins/{repo}")
                
                shutil.move(temp_dir, f"./local/plugins/{repo}")
                
                # Handle subdirectory structure
                files = os.listdir(f"./local/plugins/{repo}")
                subdir = [f for f in files if os.path.isdir(os.path.join(f"./local/plugins/{repo}", f))][0]
                if subdir != repo:
                    shutil.move(f"./local/plugins/{repo}/{subdir}", f"./local/plugins/{repo}/{repo}")
                
                return f"./local/plugins/{repo}/{repo}", root, plugin_info
                
        raise ValueError("No plugin_info.json found in repository")
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e

def check_plugin_dependencies(plugin_path):
    """Check if all plugin dependencies are met.
    
    Args:
        plugin_path (str): Path to plugin directory
        
    Returns:
        bool: True if all dependencies are met
    """
    requirements_file = os.path.join(plugin_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            requirements = f.read().splitlines()
        for requirement in requirements:
            try:
                pkg_require(requirement)
            except:
                return False
    return True

def install_plugin_dependencies(plugin_path):
    """Install plugin dependencies from requirements.txt.
    
    Args:
        plugin_path (str): Path to plugin directory
        
    Returns:
        bool: True if installation successful
    """
    requirements_file = os.path.join(plugin_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
            return True
        except subprocess.CalledProcessError:
            return False
    return True

async def plugin_install(plugin_name, source='pypi', source_path=None, remote_source=None):
    """Install a plugin from various sources.
    
    Args:
        plugin_name (str): Name of the plugin
        source (str): Installation source ('pypi', 'local', 'github')
        source_path (str, optional): Path or GitHub repo reference
        remote_source (str, optional): Remote source for the plugin (e.g., GitHub repo path)
        
    Returns:
        bool: True if installation successful
    """
    try:
        if source == 'local':
            if not source_path:
                raise ValueError("source_path is required for local installation")
            if not os.path.isfile(os.path.join(source_path, 'setup.py')) and \
               not os.path.isfile(os.path.join(source_path, 'pyproject.toml')):
                raise ValueError(f"Invalid Python project: no setup.py or pyproject.toml found")
            
            # Try to read plugin_info.json
            plugin_info = None
            plugin_info_path = os.path.join(source_path, 'plugin_info.json')
            if os.path.exists(plugin_info_path):
                with open(plugin_info_path, 'r') as f:
                    plugin_info = json.load(f)
            
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', source_path])
            update_plugin_manifest(plugin_name, 'local', source_path, metadata=plugin_info)
            
        elif source == 'pypi':
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', plugin_name])
            update_plugin_manifest(plugin_name, 'pypi', None)
            
        elif source == 'github':
            if not source_path:
                raise ValueError("source_path (repo/name[:tag]) required for GitHub installation")
            
            parts = source_path.split(':')
            repo_path = parts[0]
            tag = parts[1] if len(parts) > 1 else None
            
            plugin_dir, _, plugin_info = download_github_files(repo_path, tag)
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', plugin_dir])
            
            update_plugin_manifest(
                plugin_info['name'],
                'github',
                os.path.abspath(plugin_dir),
                remote_source=repo_path,
                version=plugin_info.get('version', '0.0.1'), 
                metadata=plugin_info
            )
            
        else:
            raise ValueError(f"Unsupported installation source: {source}")
        
        return True

    except Exception as e:
        raise RuntimeError(f"Plugin installation failed: {str(e)}")

def plugin_update(plugin_name):
    """Update an installed plugin.
    
    Args:
        plugin_name (str): Name of the plugin to update
        
    Returns:
        bool: True if update successful
    """
    # This is a synchronous function that can't use the async plugin_install directly
    try:
        # Just use pip directly for now
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', plugin_name])
        return True
    except Exception as e:
        print(f"Error updating plugin {plugin_name}: {str(e)}")
        return False

# Import pkg_resources here to avoid circular imports
async def install_recommended_plugins(agent_name, context=None):
    """
    Install plugins recommended for an agent based on its required_plugins list.
    
    Args:
        agent_name (str): Name of the agent
        
    Returns:
        dict: Results of plugin installation
    """
    try:
        # Load agent data
        from pathlib import Path
        agent_path = f"data/agents/local/{agent_name}/agent.json"
        if not os.path.exists(agent_path):
            agent_path = f"data/agents/shared/{agent_name}/agent.json"
            
        if not os.path.exists(agent_path):
            return {"error": f"Agent {agent_name} not found"}
            
        with open(agent_path, 'r') as f:
            agent_data = json.load(f)
            
        # Get recommended plugins (check both fields for backward compatibility)
        recommended_plugins = agent_data.get('recommended_plugins', agent_data.get('required_plugins', []))

        # Get plugin sources from check_recommended_plugins endpoint
        from fastapi import HTTPException
        try:
            # Implement the same logic as check_recommended_plugins directly here
            # to avoid circular imports
            plugin_info = {}
            plugin_sources = {}
            
            # Define indices directory path
            # Try multiple possible locations for indices
            possible_locations = [
                Path("indices"),
                Path("data/indices"),
                Path(os.getcwd()) / "indices",
                Path(os.getcwd()).parent / "indices",
                Path("/files/mindroot/indices")
            ]
            
            indices_dir = None
            
            # Determine which indices directory exists
            for location in possible_locations:
                print(f"Checking for indices in: {location}")
                if location.exists():
                    # Check if it has any .json files
                    indices_dir = location if any(location.glob("*.json")) else None
                    print(f"Found indices directory at: {indices_dir} with {len(list(location.glob('*.json')))} JSON files")
                    break
            
            if not indices_dir:
                print("WARNING: Could not find indices directory in any of the expected locations")
                indices_dir = Path("indices")  # Fallback to default            
            # Get all available indices
            available_indices = []
            for index_file in indices_dir.glob("*.json"):
                # Also try looking for indices in subdirectories
                print(f"Found index file: {index_file}")
                
                try:
                    print(f"Reading index file for plugin sources: {index_file}")
                    with open(index_file, 'r') as f:
                        index_data = json.load(f)
                        available_indices.append(index_data)
                except Exception as e:
                    print(f"Error reading index file {index_file}: {str(e)}")
            
            # Also check for indices in subdirectories
            for subdir in indices_dir.glob("*/"):
                # Also try looking for indices in subdirectories
                print(f"Checking for index files in subdirectory: {subdir}")
                
                # Look for index.json in the subdirectory
                index_file_path = subdir / "index.json"
                if index_file_path.exists():
                    try:
                        print(f"Reading index file: {index_file_path}")
                        with open(index_file_path, 'r') as f:
                            index_data = json.load(f)
                            available_indices.append(index_data)
                    except Exception as e:
                        print(f"Error reading index file {index_file_path}: {str(e)}")
                else:
                    print(f"No index.json found in {subdir}")
            
            print(f"Found {len(available_indices)} indices with {sum(len(index.get('plugins', [])) for index in available_indices)} total plugins")
            
            # Look for each recommended plugin in the indices
            print(f"Looking for recommended plugins: {recommended_plugins}")
            for plugin_name in recommended_plugins:
                for index in available_indices:
                    for plugin in index.get('plugins', []):
                        print(f"Checking plugin {plugin.get('name')} against {plugin_name}")
                        if plugin.get('name') == plugin_name:
                            # Found the plugin in an index
                            remote_source = plugin.get('remote_source')
                            print(f"Found plugin {plugin_name} in index with remote_source: {remote_source}")
                            github_url = plugin.get('github_url')
                            print(f"Found plugin {plugin_name} in index with github_url: {github_url}")
                            
                            if github_url and 'github.com/' in github_url:
                                github_path = github_url.split('github.com/')[1]
                                print(f"Extracted GitHub path for {plugin_name}: {github_path}")
                                plugin_sources[plugin_name] = github_path
                            elif remote_source:
                                plugin_sources[plugin_name] = remote_source
            print(f"Found plugin sources: {plugin_sources}")
            
            plugin_info = {"plugin_sources": plugin_sources}
            plugin_sources = plugin_info.get("plugin_sources", {}) if plugin_info else {}
        except Exception as e:
            trace = traceback.format_exc()
            print(f"Error getting plugin sources: {str(e)} {trace}")
            plugin_sources = {}
        
        # Install each recommended plugin
        results = []
        for plugin_name in recommended_plugins:
            # Check if plugin is already installed
            try:
                # Try to import the plugin to check if it's installed
                try:
                    # Use pkg_resources to check if package is installed
                    import pkg_resources
                    pkg_resources.get_distribution(plugin_name)
                    # Plugin is already installed
                    results.append({"plugin": plugin_name, "status": "already_installed"})
                except pkg_resources.DistributionNotFound:
                    # Plugin is not installed, get source info and install it
                    try:
                        # Get the source information for this plugin
                        source_info = plugin_sources.get(plugin_name, plugin_name)
                        
                        print(f"Installing plugin {plugin_name} from source: {source_info}")
                        # Determine installation source and path
                        if '/' in source_info:  # GitHub repo format (user/repo)
                            source = 'github'
                            source_path = source_info
                            remote_source = source_info
                        else:  # PyPI package
                            source = 'pypi'
                            source_path = None
                            remote_source = None
                        
                        # Install the plugin
                        await plugin_install(
                            plugin_name,
                            source,
                            source_path,
                            remote_source
                        )
                        
                        results.append({
                            "plugin": plugin_name,
                            "status": "success",
                            "source": source,
                            "source_path": source_path
                        })
                    except Exception as e:
                        results.append({
                            "plugin": plugin_name,
                            "status": "error",
                            "message": str(e),
                            "source_info": source_info
                        })
            except Exception as e:
                results.append({
                    "plugin": plugin_name,
                    "status": "error",
                    "message": f"Error checking installation: {str(e)}"
                })
                
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}

