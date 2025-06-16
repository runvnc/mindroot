#!/usr/bin/env python3
"""
Test script to verify the plugin manifest bug fixes.

This script simulates the conditions that could cause the manifest bug
and verifies that the fixes work correctly.
"""

import os
import sys
import json
import shutil
import tempfile
import logging
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_environment():
    """Create a temporary test environment."""
    test_dir = tempfile.mkdtemp(prefix='manifest_test_')
    logger.info(f"Created test environment: {test_dir}")
    return test_dir

def create_custom_manifest(test_dir):
    """Create a custom manifest in the root directory."""
    custom_manifest = {
        "plugins": {
            "core": {
                "chat": {"enabled": True, "source": "core"},
                "agent": {"enabled": True, "source": "core"},
                "admin": {"enabled": True, "source": "core"},
                "custom_plugin": {"enabled": True, "source": "core", "custom_setting": "test_value"}
            },
            "installed": {
                "my_custom_plugin": {
                    "enabled": True,
                    "source": "local",
                    "version": "1.2.3",
                    "custom_data": "important_user_data"
                }
            }
        }
    }
    
    manifest_path = os.path.join(test_dir, 'plugin_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(custom_manifest, f, indent=2)
    
    logger.info(f"Created custom manifest: {manifest_path}")
    return custom_manifest

def test_migration_scenario(test_dir, custom_manifest):
    """Test the migration scenario."""
    logger.info("\n=== Testing Migration Scenario ===")
    
    # Change to test directory
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        # Import the fixed manifest module
        from mindroot.lib.plugins.manifest import load_plugin_manifest, _get_absolute_paths
        
        # Verify paths
        manifest_abs_path, root_manifest_abs_path, data_dir_abs_path = _get_absolute_paths()
        logger.info(f"Manifest path: {manifest_abs_path}")
        logger.info(f"Root manifest path: {root_manifest_abs_path}")
        logger.info(f"Data dir path: {data_dir_abs_path}")
        
        # Load manifest (should trigger migration)
        loaded_manifest = load_plugin_manifest()
        
        # Verify migration worked
        assert os.path.exists(manifest_abs_path), "Manifest should exist in data directory"
        assert not os.path.exists(root_manifest_abs_path), "Root manifest should be moved"
        
        # Verify content preservation
        assert 'my_custom_plugin' in loaded_manifest['plugins']['installed'], "Custom plugin should be preserved"
        assert loaded_manifest['plugins']['installed']['my_custom_plugin']['custom_data'] == 'important_user_data', "Custom data should be preserved"
        
        logger.info("✅ Migration scenario passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration scenario failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def test_corruption_recovery_scenario(test_dir):
    """Test recovery from corrupted manifest."""
    logger.info("\n=== Testing Corruption Recovery Scenario ===")
    
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        from mindroot.lib.plugins.manifest import load_plugin_manifest, _get_absolute_paths
        
        manifest_abs_path, _, data_dir_abs_path = _get_absolute_paths()
        
        # Create corrupted manifest
        os.makedirs(data_dir_abs_path, exist_ok=True)
        with open(manifest_abs_path, 'w') as f:
            f.write('{"invalid": json content')
        
        logger.info(f"Created corrupted manifest: {manifest_abs_path}")
        
        # Load manifest (should recover from corruption)
        loaded_manifest = load_plugin_manifest()
        
        # Verify recovery
        assert isinstance(loaded_manifest, dict), "Should return valid dict"
        assert 'plugins' in loaded_manifest, "Should have plugins key"
        
        # Check for backup
        backup_files = [f for f in os.listdir(data_dir_abs_path) if f.startswith('plugin_manifest.json.backup_')]
        assert len(backup_files) > 0, "Should create backup of corrupted file"
        
        logger.info(f"✅ Corruption recovery scenario passed (created {len(backup_files)} backup files)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Corruption recovery scenario failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def test_atomic_write_scenario(test_dir):
    """Test atomic write operations."""
    logger.info("\n=== Testing Atomic Write Scenario ===")
    
    original_cwd = os.getcwd()
    os.chdir(test_dir)
    
    try:
        from mindroot.lib.plugins.manifest import save_plugin_manifest, load_plugin_manifest
        
        # Create initial manifest
        initial_manifest = {
            "plugins": {
                "core": {"test": {"enabled": True}},
                "installed": {}
            }
        }
        
        save_plugin_manifest(initial_manifest)
        
        # Verify it was saved
        loaded = load_plugin_manifest()
        assert loaded['plugins']['core']['test']['enabled'] == True
        
        # Update manifest
        updated_manifest = {
            "plugins": {
                "core": {"test": {"enabled": False}, "test2": {"enabled": True}},
                "installed": {"new_plugin": {"enabled": True}}
            }
        }
        
        save_plugin_manifest(updated_manifest)
        
        # Verify update
        loaded = load_plugin_manifest()
        assert loaded['plugins']['core']['test']['enabled'] == False
        assert 'test2' in loaded['plugins']['core']
        assert 'new_plugin' in loaded['plugins']['installed']
        
        logger.info("✅ Atomic write scenario passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Atomic write scenario failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def main():
    """Run all test scenarios."""
    logger.info("Starting plugin manifest fix tests...")
    
    test_dir = create_test_environment()
    
    try:
        # Test 1: Migration scenario
        custom_manifest = create_custom_manifest(test_dir)
        migration_passed = test_migration_scenario(test_dir, custom_manifest)
        
        # Clean up for next test
        shutil.rmtree(test_dir)
        test_dir = create_test_environment()
        
        # Test 2: Corruption recovery
        corruption_passed = test_corruption_recovery_scenario(test_dir)
        
        # Test 3: Atomic writes
        atomic_passed = test_atomic_write_scenario(test_dir)
        
        # Summary
        logger.info("\n=== Test Results ===")
        logger.info(f"Migration scenario: {'✅ PASSED' if migration_passed else '❌ FAILED'}")
        logger.info(f"Corruption recovery: {'✅ PASSED' if corruption_passed else '❌ FAILED'}")
        logger.info(f"Atomic write: {'✅ PASSED' if atomic_passed else '❌ FAILED'}")
        
        all_passed = migration_passed and corruption_passed and atomic_passed
        logger.info(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return 0 if all_passed else 1
        
    finally:
        # Clean up
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            logger.info(f"Cleaned up test environment: {test_dir}")

if __name__ == '__main__':
    sys.exit(main())
