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

def plugin_install(plugin_name, source='pypi', source_path=None):
    """Install a plugin from various sources.
    
    Args:
        plugin_name (str): Name of the plugin
        source (str): Installation source ('pypi', 'local', 'github')
        source_path (str, optional): Path or GitHub repo reference
        
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
    return plugin_install(plugin_name)
