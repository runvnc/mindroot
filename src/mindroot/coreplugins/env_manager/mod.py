import os
import re
import json
import subprocess
from pathlib import Path
from lib.providers.services import service
from lib.plugins import list_enabled, get_plugin_path


def should_skip_directory(directory):
    """Check if a directory should be skipped during scanning.
    
    Args:
        directory (str): Path to check
        
    Returns:
        bool: True if the directory should be skipped, False otherwise
    """
    # Directories to skip
    skip_dirs = [
        '__pycache__', 
        'node_modules', 
        'static/js', 
        'static/css',
        'venv',
        'env',
        '.env',
        'virtualenv',
        'site-packages',
        'dist-packages',
        '.git',
        '.idea',
        '.vscode',
        'build',
        'dist',
        'egg-info'
    ]
    
    # Check if any part of the path contains a directory to skip
    path_parts = Path(directory).parts
    for skip_dir in skip_dirs:
        if skip_dir in path_parts:
            return True
            
    return False


def scan_directory_for_env_vars(directory):
    """Scan a directory for environment variable references using grep.
    
    Args:
        directory (str): Path to the directory to scan
        
    Returns:
        set: Set of environment variable names found
    """
    env_vars = set()
    
    # Skip if this is a directory we should ignore
    if should_skip_directory(directory):
        return env_vars
    
    try:
        # Use grep to find os.environ references - much faster than parsing each file
        cmd = [
            'grep', '-r', 
            '-E', "(os\.environ\[\"|'|os\.environ\.get\(\"|')", 
            '--include=*.py', 
            '--exclude-dir=venv', 
            '--exclude-dir=env',
            '--exclude-dir=.env',
            '--exclude-dir=site-packages',
            '--exclude-dir=dist-packages',
            '--exclude-dir=__pycache__',
            '--exclude-dir=node_modules',
            directory
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode not in [0, 1]:  # 0 = matches found, 1 = no matches
            print(f"Error running grep on {directory}: {result.stderr}")
            return env_vars
            
        # Extract variable names using regex
        pattern1 = r"os\.environ\.get\(['\"]([A-Za-z0-9_]+)['\"]"  # os.environ.get('VAR_NAME')
        pattern2 = r"os\.environ\[['\"]([A-Za-z0-9_]+)['\"]\]"    # os.environ['VAR_NAME']
        
        for line in result.stdout.splitlines():
            for pattern in [pattern1, pattern2]:
                for match in re.finditer(pattern, line):
                    var_name = match.group(1)
                    env_vars.add(var_name)
    
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")
    
    return env_vars

@service()
async def scan_env_vars(params=None, context=None):
    """Scan all enabled plugins for environment variable references.
    
    Returns:
        dict: Dictionary with plugin names as keys and environment variable info as values
    """
    results = {}
    all_env_vars = set()
    
    # Get all enabled plugins
    enabled_plugins = list_enabled()
    
    for plugin_name, category in enabled_plugins:
        plugin_path = get_plugin_path(plugin_name)
        if plugin_path:
            # If plugin_path is a file, get its directory
            if os.path.isfile(plugin_path):
                plugin_path = os.path.dirname(plugin_path)
                
            # Skip scanning if this is a directory we should ignore
            if should_skip_directory(plugin_path):
                continue
                
            # Scan the plugin directory for environment variable references
            env_vars = scan_directory_for_env_vars(plugin_path)
            
            if env_vars:
                results[plugin_name] = {
                    'plugin_name': plugin_name,
                    'category': category,
                    'env_vars': list(env_vars)
                }
                all_env_vars.update(env_vars)
    
    # Get current environment variables
    current_env = {}
    for var_name in all_env_vars:
        if var_name in os.environ:
            # Mask sensitive values
            if any(sensitive in var_name.lower() for sensitive in ['key', 'secret', 'password', 'token']):  
                current_env[var_name] = '********'
            else:
                current_env[var_name] = os.environ[var_name]
        else:
            # Include variables not in environment with empty value
            current_env[var_name] = ''
    
    # Add current environment variables to results
    results['current_env'] = current_env
    
    return results


def load_env_file():
    """Load environment variables from .env file.
    
    Returns:
        dict: Dictionary of environment variables from .env file
    """
    env_vars = {}
    env_file = '.env'
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    
    return env_vars


def save_env_file(env_vars):
    """Save environment variables to .env file.
    
    Args:
        env_vars (dict): Dictionary of environment variables to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load existing .env file to preserve variables not being updated
        existing_vars = load_env_file()
        
        # Update with new values
        existing_vars.update(env_vars)
        
        # Write to .env file
        with open('.env', 'w') as f:
            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")
        
        return True
    except Exception as e:
        print(f"Error saving .env file: {e}")
        return False


@service()
async def update_env_var(var_name, var_value, context=None):
    """Update an environment variable.
    
    Args:
        var_name (str): Name of the environment variable
        var_value (str): Value to set
        
    Returns:
        dict: Status of the operation
    """
    try:
        # Update the environment variable in the current process
        os.environ[var_name] = var_value
        
        # Save to .env file for persistence across restarts
        save_success = save_env_file({var_name: var_value})
        
        return {
            'success': True,
            'message': f"Environment variable {var_name} updated successfully" + 
                      (" and saved to .env file" if save_success else "")
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Error updating environment variable: {str(e)}"
        }
