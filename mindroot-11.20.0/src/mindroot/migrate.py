import os
import logging
from .lib.plugins.manifest import create_default_plugin_manifest, _get_absolute_paths, _validate_manifest

# Setup logging
logger = logging.getLogger(__name__)

def migrate_plugin_manifest():
    """Migrate plugin_manifest.json from root to data/ directory if needed.
    
    This function now delegates to the consolidated manifest handling logic.
    """
    manifest_abs_path, root_manifest_abs_path, _ = _get_absolute_paths()
    
    logger.info("Checking plugin manifest migration...")
    logger.debug(f"Target manifest path: {manifest_abs_path}")
    logger.debug(f"Source manifest path: {root_manifest_abs_path}")
    
    # Check if target manifest already exists and is valid
    is_valid, _ = _validate_manifest(manifest_abs_path)
    if is_valid:
        logger.info(f"Valid plugin manifest already exists at {manifest_abs_path}")
        return
    
    # Check if source manifest exists
    source_exists = os.path.exists(root_manifest_abs_path)
    if source_exists:
        logger.info(f"Found manifest to migrate from {root_manifest_abs_path}")
    else:
        logger.info("No existing plugin manifest found to migrate")
    
    # Use the consolidated manifest creation logic which handles migration
    try:
        create_default_plugin_manifest()
        logger.info("Plugin manifest migration/creation completed successfully")
    except Exception as e:
        logger.error(f"Plugin manifest migration failed: {e}")
        raise

def run_migrations():
    """Run all necessary migrations."""
    logger.info("Running MindRoot migrations...")
    try:
        migrate_plugin_manifest()
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Don't raise here - let the system continue with default manifest
        logger.warning("Continuing with default manifest due to migration failure")
