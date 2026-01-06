import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

class APIKeyManager:
    def __init__(self, keys_dir: str = "data/apikeys"):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self._load_keys()

    def _load_keys(self) -> None:
        """Load all API keys from storage"""
        self.keys = {}
        for key_file in self.keys_dir.glob("*.json"):
            try:
                with open(key_file, 'r') as f:
                    key_data = json.load(f)
                    self.keys[key_data['key']] = key_data
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in key file: {key_file}")
            except Exception as e:
                print(f"Error loading key file {key_file}: {e}")

    def create_key(self, username: str, description: str = "") -> Dict:
        """Create a new API key for a user
        
        Args:
            username: The username to associate with the key
            description: Optional description for the key
            
        Returns:
            Dict containing the key details
        """
        api_key = str(uuid.uuid4())
        key_data = {
            "key": api_key,
            "username": username,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to file
        key_file = self.keys_dir / f"{api_key}.json"
        with open(key_file, 'w') as f:
            json.dump(key_data, f, indent=4)
        
        self.keys[api_key] = key_data
        return key_data

    def validate_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return associated data if valid
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dict containing the key details if valid, None otherwise
        """
        print(f"Validating key: {api_key}")
        print("My keys are", self.keys)
        return self.keys.get(api_key)

    def delete_key(self, api_key: str) -> bool:
        """Delete an API key
        
        Args:
            api_key: The API key to delete
            
        Returns:
            bool: True if key was deleted, False if key not found
        """
        if api_key in self.keys:
            key_file = self.keys_dir / f"{api_key}.json"
            try:
                key_file.unlink(missing_ok=True)
                del self.keys[api_key]
                return True
            except Exception as e:
                print(f"Error deleting key file {key_file}: {e}")
                return False
        return False

    def list_keys(self, username: Optional[str] = None) -> List[Dict]:
        """List all API keys or keys for specific user
        
        Args:
            username: Optional username to filter keys by
            
        Returns:
            List of key data dictionaries
        """
        if username:
            return [k for k in self.keys.values() if k['username'] == username]
        return list(self.keys.values())

# Global instance
api_key_manager = APIKeyManager()
