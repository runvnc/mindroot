import os
import shutil
from pathlib import Path

def migrate_plugin_manifest():
    """Migrate plugin_manifest.json from root to data/ directory if needed."""
    root_manifest = 'plugin_manifest.json'
    data_manifest = 'data/plugin_manifest.json'
    
    # If the new location already exists, no migration needed
    if os.path.exists(data_manifest):
        print(f"Plugin manifest already exists at {data_manifest}")
        return
    
    # If old location exists, move it to new location
    if os.path.exists(root_manifest):
        print(f"Migrating plugin manifest from {root_manifest} to {data_manifest}")
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        # Move the file
        shutil.move(root_manifest, data_manifest)
        print(f"Plugin manifest migration complete")
    else:
        print("No existing plugin manifest found to migrate")

def run_migrations():
    """Run all necessary migrations."""
    print("Running MindRoot migrations...")
    migrate_plugin_manifest()
    print("Migrations complete")
