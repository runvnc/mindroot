import os
import re
import json
import subprocess
from pathlib import Path
from lib.providers.services import service
import lib
from lib.plugins import list_enabled, get_plugin_path
import mindroot.coreplugins


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
        'dist-packages',
        '.git',
        '.idea',
        '.vscode',
        'build',
        'dist',
        'egg-info'
    ]
    
    # Special handling for site-packages - only skip if it's not mindroot related
    if 'site-packages' in directory:
        # Allow mindroot core plugins in site-packages
        if 'mindroot/coreplugins' in directory or 'mindroot/lib' in directory:
            return False
        # Skip other site-packages content
        return True
    
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
            '-E', r"(os\.environ(\.get\(|\[)|os\.getenv\(|getenv\()", 
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
        patterns = [
            r"os\.environ\.get\(['\"]([A-Za-z0-9_]+)['\"]",  # os.environ.get('VAR_NAME')
            r"os\.environ\[['\"]([A-Za-z0-9_]+)['\"]\]",    # os.environ['VAR_NAME']
            r"os\.getenv\(['\"]([A-Za-z0-9_]+)['\"]",      # os.getenv('VAR_NAME')
            r"(?<!os\.)getenv\(['\"]([A-Za-z0-9_]+)['\"]",  # getenv('VAR_NAME') without os. prefix
        ]
        
        for line in result.stdout.splitlines():
            # Skip lines that are comments containing example patterns
            if '# os.environ.get(' in line or '# os.environ[' in line or '# os.getenv(' in line:
                continue
            
            for pattern in patterns:
                for match in re.finditer(pattern, line):
                    var_name = match.group(1)
                    # Filter out obvious false positives
                    if var_name not in ['VAR_NAME', 'VARIABLE_NAME', 'ENV_VAR']:
                        env_vars.add(var_name)
    
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")
    
    return env_vars

@service()
async def scan_env_vars(params=None, context=None):
    """Scan all enabled plugins for environment variable references.
    
    Debug logs added to help troubleshoot path resolution and scanning.
    
    Returns:
        dict: Dictionary with plugin names as keys and environment variable info as values
    """
    results = {}
    all_env_vars = set()
    
    print("[ENV_MANAGER DEBUG] Starting scan_env_vars")
    print(f"[ENV_MANAGER DEBUG] Current working directory: {os.getcwd()}")
    
    # Get all enabled plugins
    enabled_plugins = list_enabled()
    print(f"[ENV_MANAGER DEBUG] Found {len(enabled_plugins)} enabled plugins: {[name for name, cat in enabled_plugins]}")
    
    for plugin_name, category in enabled_plugins:
        plugin_path = get_plugin_path(plugin_name)
        print(f"[ENV_MANAGER DEBUG] Plugin {plugin_name}: path = {plugin_path}")
        if plugin_path:
            # If plugin_path is a file, get its directory
            if os.path.isfile(plugin_path):
                plugin_path = os.path.dirname(plugin_path)
                print(f"[ENV_MANAGER DEBUG] Plugin {plugin_name}: converted to directory = {plugin_path}")
                
            # Skip scanning if this is a directory we should ignore
            if should_skip_directory(plugin_path):
                print(f"[ENV_MANAGER DEBUG] Plugin {plugin_name}: skipping directory {plugin_path}")
                continue
                
            # Scan the plugin directory for environment variable references
            env_vars = scan_directory_for_env_vars(plugin_path)
            print(f"[ENV_MANAGER DEBUG] Plugin {plugin_name}: found {len(env_vars)} env vars: {sorted(env_vars)}")
            
            if env_vars:
                results[plugin_name] = {
                    'plugin_name': plugin_name,
                    'category': category,
                    'env_vars': list(env_vars)
                }
                all_env_vars.update(env_vars)
        else:
            print(f"[ENV_MANAGER DEBUG] Plugin {plugin_name}: no path found")
    
    # Also scan the lib directory (but not coreplugins since individual plugins are already scanned)
    lib_path = os.path.dirname(lib.__file__)
    
    print(f"[ENV_MANAGER DEBUG] lib.__file__ = {lib.__file__}")
    print(f"[ENV_MANAGER DEBUG] lib_path = {lib_path}")
    
    # Scan lib directory for additional core variables
    if os.path.isdir(lib_path):
        print(f"[ENV_MANAGER DEBUG] Scanning lib directory: {lib_path}")
        lib_vars = scan_directory_for_env_vars(lib_path)
        print(f"[ENV_MANAGER DEBUG] Lib vars found: {sorted(lib_vars)}")
        
        if lib_vars:
            results['lib'] = {
                'plugin_name': 'lib',
                'category': 'core',
                'env_vars': sorted(list(lib_vars))
            }
            all_env_vars.update(lib_vars)
            print(f"[ENV_MANAGER DEBUG] Added lib section to results")
    else:
        print(f"[ENV_MANAGER DEBUG] Lib directory not found: {lib_path}")

    # Note: We don't scan the entire coreplugins directory separately because
    # individual core plugins are already being scanned above in the enabled_plugins loop.
    # This prevents duplicate entries that would show up as "Multiple Plugins".

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
    
    print(f"[ENV_MANAGER DEBUG] Results structure: {[(k, len(v.get('env_vars', [])) if isinstance(v, dict) and 'env_vars' in v else 'N/A') for k, v in results.items()]}")
    
    print(f"[ENV_MANAGER DEBUG] Final results keys: {list(results.keys())}")
    print(f"[ENV_MANAGER DEBUG] Total unique env vars: {len(all_env_vars)}")
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
