import json
import nanoid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

class WidgetManager:
    """Manages secure widget tokens for chat embedding."""
    
    def __init__(self, widgets_dir: str = "data/widgets"):
        self.widgets_dir = Path(widgets_dir)
        self.widgets_dir.mkdir(parents=True, exist_ok=True)
        self._load_widgets()
    
    def _load_widgets(self) -> None:
        """Load all widget tokens from storage."""
        self.widgets = {}
        for widget_file in self.widgets_dir.glob("*.json"):
            try:
                with open(widget_file, 'r') as f:
                    widget_data = json.load(f)
                    self.widgets[widget_data['token']] = widget_data
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in widget file: {widget_file}")
            except Exception as e:
                print(f"Error loading widget file {widget_file}: {e}")
    
    def create_widget_token(self, api_key: str, agent_name: str, base_url: str, 
                           created_by: str, description: str = "", 
                           styling: Optional[Dict] = None) -> str:
        """Create a new widget token and store its configuration.
        
        Args:
            api_key: The API key to use for authentication
            agent_name: The agent to use for chat sessions
            base_url: The base URL for the MindRoot instance
            created_by: Username of the creator
            description: Optional description for the widget
            styling: Optional styling configuration
            
        Returns:
            The generated widget token
        """
        token = nanoid.generate()
        
        if styling is None:
            styling = {
                "position": "bottom-right",
                "theme": "dark",
                "width": "400px",
                "height": "600px"
            }
        
        widget_data = {
            "token": token,
            "api_key": api_key,
            "agent_name": agent_name,
            "base_url": base_url,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": created_by,
            "description": description,
            "styling": styling
        }
        
        # Save to file
        widget_file = self.widgets_dir / f"{token}.json"
        with open(widget_file, 'w') as f:
            json.dump(widget_data, f, indent=2)
        
        self.widgets[token] = widget_data
        return token
    
    def get_widget_config(self, token: str) -> Optional[Dict]:
        """Retrieve widget configuration by token.
        
        Args:
            token: The widget token
            
        Returns:
            Widget configuration dict if found, None otherwise
        """
        return self.widgets.get(token)
    
    def delete_widget_token(self, token: str) -> bool:
        """Delete a widget token and its configuration.
        
        Args:
            token: The widget token to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        if token in self.widgets:
            widget_file = self.widgets_dir / f"{token}.json"
            try:
                widget_file.unlink(missing_ok=True)
                del self.widgets[token]
                return True
            except Exception as e:
                print(f"Error deleting widget file {widget_file}: {e}")
                return False
        return False
    
    def list_widget_tokens(self, created_by: Optional[str] = None) -> List[Dict]:
        """List all widget tokens, optionally filtered by creator.
        
        Args:
            created_by: Optional username to filter by
            
        Returns:
            List of widget configurations (with API keys hidden)
        """
        widgets = []
        
        for widget_data in self.widgets.values():
            # Filter by creator if specified
            if created_by and widget_data.get("created_by") != created_by:
                continue
            
            # Create safe copy without exposing API key
            safe_widget = widget_data.copy()
            safe_widget["api_key"] = "***hidden***"
            widgets.append(safe_widget)
        
        return sorted(widgets, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def validate_token(self, token: str) -> bool:
        """Check if a widget token is valid.
        
        Args:
            token: The widget token to validate
            
        Returns:
            True if valid, False otherwise
        """
        return token in self.widgets

# Global widget manager instance
widget_manager = WidgetManager()
