#!/usr/bin/env python3
"""
Quick fix script to mark the calculator server as installed.
"""

import json
import sys
from pathlib import Path

def fix_calculator_server():
    config_file = Path("/tmp/mcp_servers.json")
    
    if not config_file.exists():
        print("Config file not found")
        return False
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check if calculator server exists
        if "calculator" not in config:
            print("Calculator server not found in config")
            return False
        
        # Mark as installed
        config["calculator"]["installed"] = True
        
        # Write back to file
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Calculator server marked as installed")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_calculator_server()
    sys.exit(0 if success else 1)
