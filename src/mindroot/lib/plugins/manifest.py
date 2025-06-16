import json
import os
import shutil
import tempfile
import logging
from datetime import datetime
from pathlib import Path

# Central definition of manifest file location
MANIFEST_FILE = 'data/plugin_manifest.json'

# Setup logging
logger = logging.getLogger(__name__)

def _get_absolute_paths():
    """Get absolute paths for all manifest-related files.
    
    Returns:
        tuple: (manifest_abs_path, root_manifest_abs_path, data_dir_abs_path)
    """
    cwd = os.getcwd()
    manifest_abs_path = os.path.abspath(os.path.join(cwd, MANIFEST_FILE))
    root_manifest_abs_path = os.path.abspath(os.path.join(cwd, 'plugin_manifest.json'))
    data_dir_abs_path = os.path.abspath(os.path.join(cwd, 'data'))
    
    return manifest_abs_path, root_manifest_abs_path, data_dir_abs_path

def _backup_manifest(manifest_path):
    """Create a backup of the existing manifest file.
    
    Args:
        manifest_path (str): Absolute path to the manifest file
        
    Returns:
        str: Path to backup file, or None if backup failed
    """
    if not os.path.exists(manifest_path):
        return None
        
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{manifest_path}.backup_{timestamp}"
        shutil.copy2(manifest_path, backup_path)
        logger.info(f"Created manifest backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create manifest backup: {e}")
        return None

def _atomic_write_manifest(manifest_path, manifest_data):
    """Atomically write manifest data to file.
    
    Args:
        manifest_path (str): Absolute path to the manifest file
        manifest_data (dict): Manifest data to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', 
                                       dir=os.path.dirname(manifest_path), 
                                       delete=False) as tmp_file:
            json.dump(manifest_data, tmp_file, indent=2)
            tmp_path = tmp_file.name
        
        # Atomic move to final location
        shutil.move(tmp_path, manifest_path)
        logger.debug(f"Atomically wrote manifest to: {manifest_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to atomically write manifest: {e}")
        # Clean up temp file if it exists
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass
        return False

def _validate_manifest(manifest_path):
    """Validate that a manifest file exists and contains valid JSON.
    
    Args:
        manifest_path (str): Absolute path to the manifest file
        
    Returns:
        tuple: (is_valid, manifest_data_or_none)
    """
    if not os.path.exists(manifest_path):
        return False, None
        
    try:
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
            
        # Basic structure validation
        if not isinstance(manifest_data, dict):
            logger.warning(f"Manifest is not a dict: {manifest_path}")
            return False, None
            
        if 'plugins' not in manifest_data:
            logger.warning(f"Manifest missing 'plugins' key: {manifest_path}")
            return False, None
            
        return True, manifest_data
        
    except json.JSONDecodeError as e:
        logger.warning(f"Manifest contains invalid JSON: {manifest_path} - {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error validating manifest: {manifest_path} - {e}")
        return False, None

def _migrate_manifest_from_root():
    """Migrate manifest from root directory to data directory if needed.
    
    This function consolidates the migration logic and uses absolute paths.
    
    Returns:
        bool: True if migration was successful or not needed, False if failed
    """
    manifest_abs_path, root_manifest_abs_path, data_dir_abs_path = _get_absolute_paths()
    
    logger.debug(f"Checking for manifest migration:")
    logger.debug(f"  Target: {manifest_abs_path}")
    logger.debug(f"  Source: {root_manifest_abs_path}")
    
    # If target already exists and is valid, no migration needed
    is_valid, _ = _validate_manifest(manifest_abs_path)
    if is_valid:
        logger.debug(f"Valid manifest already exists at: {manifest_abs_path}")
        return True
    
    # If target exists but is invalid, back it up
    if os.path.exists(manifest_abs_path):
        logger.warning(f"Invalid manifest found at {manifest_abs_path}, backing up")
        _backup_manifest(manifest_abs_path)
    
    # Check if source manifest exists and is valid
    is_valid, manifest_data = _validate_manifest(root_manifest_abs_path)
    if is_valid:
        logger.info(f"Migrating manifest from {root_manifest_abs_path} to {manifest_abs_path}")
        
        # Ensure data directory exists
        os.makedirs(data_dir_abs_path, exist_ok=True)
        
        # Atomic write to new location
        if _atomic_write_manifest(manifest_abs_path, manifest_data):
            # Remove old file only after successful write
            try:
                os.unlink(root_manifest_abs_path)
                logger.info(f"Successfully migrated manifest and removed old file")
                return True
            except Exception as e:
                logger.warning(f"Manifest migrated but failed to remove old file: {e}")
                return True
        else:
            logger.error(f"Failed to write migrated manifest")
            return False
    
    logger.debug(f"No valid manifest found to migrate from {root_manifest_abs_path}")
    return True  # Not an error - just no migration needed

def create_default_plugin_manifest():
    """Create a new default manifest file.
    
    This function first attempts migration, then creates from default template if needed.
    """
    manifest_abs_path, _, data_dir_abs_path = _get_absolute_paths()
    
    logger.info(f"Creating default plugin manifest at: {manifest_abs_path}")
    
    # First attempt migration from root directory
    if _migrate_manifest_from_root():
        # Check if migration was successful
        is_valid, _ = _validate_manifest(manifest_abs_path)
        if is_valid:
            logger.info(f"Manifest successfully migrated from root directory")
            return
    
    # Migration didn't work, create from default template
    logger.info(f"Creating manifest from default template")
    
    # Backup existing file if it exists (even if invalid)
    if os.path.exists(manifest_abs_path):
        _backup_manifest(manifest_abs_path)
    
    try:
        # Read default template
        default_manifest_path = os.path.join(os.path.dirname(__file__), 'default_plugin_manifest.json')
        with open(default_manifest_path, 'r') as f:
            default_manifest = json.load(f)
        
        # Ensure data directory exists
        os.makedirs(data_dir_abs_path, exist_ok=True)
        
        # Atomic write
        if _atomic_write_manifest(manifest_abs_path, default_manifest):
            logger.info(f"Successfully created default manifest")
        else:
            logger.error(f"Failed to create default manifest")
            raise Exception("Failed to write default manifest")
            
    except Exception as e:
        logger.error(f"Failed to create default manifest: {e}")
        raise

def load_plugin_manifest():
    """Load the plugin manifest file.
    
    Returns:
        dict: The manifest data structure
    """
    manifest_abs_path, _, _ = _get_absolute_paths()
    
    # Validate existing manifest
    is_valid, manifest_data = _validate_manifest(manifest_abs_path)
    
    if is_valid:
        logger.debug(f"Loaded valid manifest from: {manifest_abs_path}")
        return manifest_data
    
    # Manifest is missing or invalid, create default
    logger.warning(f"Manifest missing or invalid at {manifest_abs_path}, creating default")
    create_default_plugin_manifest()
    
    # Load the newly created manifest
    is_valid, manifest_data = _validate_manifest(manifest_abs_path)
    if is_valid:
        return manifest_data
    else:
        logger.error(f"Failed to create valid default manifest")
        raise Exception("Could not load or create valid plugin manifest")

def save_plugin_manifest(manifest):
    """Save the plugin manifest file.
    
    Args:
        manifest (dict): The manifest data structure to save
    """
    manifest_abs_path, _, _ = _get_absolute_paths()
    
    # Backup existing manifest before saving
    _backup_manifest(manifest_abs_path)
    
    # Atomic write
    if not _atomic_write_manifest(manifest_abs_path, manifest):
        logger.error(f"Failed to save plugin manifest")
        raise Exception("Failed to save plugin manifest")
    
    logger.debug(f"Successfully saved manifest to: {manifest_abs_path}")

def update_plugin_manifest(plugin_name, source, source_path, remote_source=None, version="0.0.1", metadata=None):
    """Update or add a plugin entry in the manifest.
    
    Args:
        plugin_name (str): Name of the plugin
        source (str): Source type ('core', 'local', 'github')
        source_path (str): Path to the plugin
        remote_source (str, optional): GitHub repository reference
        version (str, optional): Plugin version
        metadata (dict, optional): Plugin metadata including commands and services
    """
    manifest = load_plugin_manifest()
    category = 'installed' if source != 'core' else 'core'
    
    # Try to read plugin_info.json if metadata not provided
    if not metadata and source_path:
        plugin_info_path = os.path.join(source_path, 'plugin_info.json')
        if os.path.exists(plugin_info_path):
            try:
                with open(plugin_info_path, 'r') as f:
                    metadata = json.load(f)
            except json.JSONDecodeError:
                metadata = None
    
    manifest['plugins'][category][plugin_name] = {
        'enabled': True,
        'source': source,
        'source_path': source_path,
        'version': version,
        'commands': metadata.get('commands', []) if metadata else [],
        'services': metadata.get('services', []) if metadata else [],
        'dependencies': metadata.get('dependencies', []) if metadata else []
    }
    
    if remote_source:
        manifest['plugins'][category][plugin_name]['remote_source'] = remote_source
    
    save_plugin_manifest(manifest)

def toggle_plugin_state(plugin_name, enabled):
    """Toggle a plugin's enabled state.
    
    Args:
        plugin_name (str): Name of the plugin
        enabled (bool): New enabled state
        
    Returns:
        bool: True if successful, False if plugin not found
    """
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            manifest['plugins'][category][plugin_name]['enabled'] = enabled
            save_plugin_manifest(manifest)
            return True
    return False

def list_enabled(include_category=True):
    """List all enabled plugins.
    
    Args:
        include_category (bool): Whether to include the category in results
        
    Returns:
        list: List of enabled plugins, optionally with categories
    """
    enabled_list = []
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        for plugin_name, plugin_info in manifest['plugins'][category].items():
            if plugin_info.get('enabled'):
                if include_category:
                    enabled_list.append((plugin_name, category))
                else:
                    enabled_list.append(plugin_name)
    return enabled_list
