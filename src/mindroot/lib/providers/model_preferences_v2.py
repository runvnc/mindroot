import json
import os
import shutil
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class ModelPreferencesV2:
    """New model preferences system supporting ordered provider/model pairs for fallback selection."""
    
    def __init__(self):
        # Use current working directory for data (supports multiple installations)
        print("Hello from Model preferences V2!")
        self.data_dir = Path.cwd() / 'data'
        self.preferences_file = self.data_dir / 'preferred_models_v2.json'
        
        # Locate template file relative to this script's location
        script_dir = Path(__file__)
        self.template_file = script_dir.parent / 'default_preferred_models.json'
        
    def ensure_preferences_exist(self) -> None:
        """Copy template preferences file to data directory if it doesn't exist."""
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        print("Ensuring preferences v2 file exists...")
        # If preferences file doesn't exist, copy from template
        if not self.preferences_file.exists():
            print("Preferences v2 file not found. Creating from template.")
            if self.template_file.exists():
                print("Copying template preferences v2 file to location data/preferred_models_v2.json")
                shutil.copy2(self.template_file, self.preferences_file)
            else:
                # Create minimal default if template doesn't exist
                default_prefs = {
                    "stream_chat": [
                        ["ah_openrouter", "deepseek/deepseek-chat-v3.1"],
                        ["ah_anthropic", "claude-sonnet-4-0"],
                        ["mr_gemini", "models/gemini-2.5-pro"], 
                        ["ah_openai", "gpt-5"]
                    ],
                    "text_to_image": [
                        ["ah_flux", "flux-dev"]
                    ]
                }
                print("Template preferences v2 file not found. Creating minimal default preferences.")
                self.save_preferences(default_prefs)
                print("File saved to data/preferred_models_v2.json")
    
    def get_preferences(self) -> Dict[str, List[List[str]]]:
        """Get preferences in new format: {service: [[provider, model], ...]}"""
        print("Getting preferences v2...")
        self.ensure_preferences_exist()
        
        try:
            with open(self.preferences_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading preferences v2: {e}")
            return {}
    
    def save_preferences(self, preferences: Dict[str, List[List[str]]]) -> None:
        """Save preferences in new format."""
        
        # Ensure data directory exists before saving
        self.data_dir.mkdir(exist_ok=True)
        
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences v2: {e}")
            raise
    
    def get_ordered_providers_for_service(self, service_name: str) -> List[Tuple[str, str]]:
        """Get ordered list of (provider, model) pairs for a service."""
        preferences = self.get_preferences()
        
        if service_name not in preferences:
            return []
        
        # Convert list of lists to list of tuples
        return [(provider, model) for provider, model in preferences[service_name]]
    
    def migrate_from_old_format(self, old_preferences: List[Dict]) -> Dict[str, List[List[str]]]:
        """Convert old format preferences to new format.
        
        Old format: [{"service_or_command_name": "stream_chat", "flag": "default", "model": "claude-3"}]
        New format: {"stream_chat": [["ah_anthropic", "claude-3.5-sonnet"]]}
        """
        new_preferences = {}
        
        for old_pref in old_preferences:
            service = old_pref.get('service_or_command_name')
            model = old_pref.get('model')
            
            if not service or not model:
                continue
            
            # For migration, we'll need to guess the provider based on model name
            # This is a best-effort conversion
            provider = self._guess_provider_from_model(model)
            
            if service not in new_preferences:
                new_preferences[service] = []
            
            # Add if not already present
            provider_model_pair = [provider, model]
            if provider_model_pair not in new_preferences[service]:
                new_preferences[service].append(provider_model_pair)
        
        return new_preferences
    
    def _guess_provider_from_model(self, model_name: str) -> str:
        """Best-effort guess of provider based on model name."""
        model_lower = model_name.lower()
        
        # Common model name patterns
        if 'claude' in model_lower:
            return 'ah_anthropic'
        elif 'gpt' in model_lower or 'chatgpt' in model_lower:
            return 'ah_openai'
        elif 'gemini' in model_lower:
            return 'mr_gemini'
        elif 'llama' in model_lower:
            return 'ah_together'  # or another llama provider
        elif 'flux' in model_lower:
            return 'ah_flux'
        elif 'stable' in model_lower or 'sd' in model_lower:
            return 'ah_stability'
        else:
            # Default fallback
            return 'unknown_provider'
    
    def add_preference(self, service: str, provider: str, model: str, position: Optional[int] = None) -> None:
        """Add a provider/model preference for a service at specified position (or end)."""
        preferences = self.get_preferences()
        
        if service not in preferences:
            preferences[service] = []
        
        provider_model_pair = [provider, model]
        
        # Remove if already exists
        preferences[service] = [pm for pm in preferences[service] if pm != provider_model_pair]
        
        # Add at specified position or end
        if position is not None and 0 <= position <= len(preferences[service]):
            preferences[service].insert(position, provider_model_pair)
        else:
            preferences[service].append(provider_model_pair)
        
        self.save_preferences(preferences)
    
    def remove_preference(self, service: str, provider: str, model: str) -> bool:
        """Remove a provider/model preference for a service. Returns True if removed."""
        preferences = self.get_preferences()
        
        if service not in preferences:
            return False
        
        provider_model_pair = [provider, model]
        
        if provider_model_pair in preferences[service]:
            preferences[service].remove(provider_model_pair)
            self.save_preferences(preferences)
            return True
        
        return False
    
    def reorder_preferences(self, service: str, ordered_pairs: List[List[str]]) -> None:
        """Set the complete ordered list of provider/model pairs for a service."""
        preferences = self.get_preferences()
        preferences[service] = ordered_pairs
        self.save_preferences(preferences)
