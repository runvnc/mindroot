from fastapi import APIRouter, HTTPException
import json
import os
from lib.route_decorators import requires_role

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

# --- Registry Settings Routes ---

@router.get("/registry/settings")
async def get_registry_settings():
    """Get registry settings including token status."""
    try:
        settings_file = 'data/registry_settings.json'
        settings = {}
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        
        # Don't return the actual token, just indicate if it's set
        return {
            "success": True,
            "data": {
                "registry_url": settings.get("registry_url", "https://registry.mindroot.io"),
                "has_token": bool(settings.get("registry_token")),
                "token_source": "file" if settings.get("registry_token") else "env" if os.getenv('REGISTRY_TOKEN') else "none"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/registry/settings")
async def update_registry_settings(settings_data: dict):
    """Update registry settings."""
    try:
        settings_file = 'data/registry_settings.json'
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load existing settings
        settings = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        
        # Update with new data
        settings.update(settings_data)
        
        # Save updated settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return {
            "success": True,
            "message": "Registry settings updated successfully.",
            "data": {
                "registry_url": settings.get("registry_url", "https://registry.mindroot.io"),
                "has_token": bool(settings.get("registry_token")),
                "token_source": "file" if settings.get("registry_token") else "env" if os.getenv('REGISTRY_TOKEN') else "none"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/registry/settings/token")
async def clear_registry_token():
    """Clear the stored registry token."""
    try:
        settings_file = 'data/registry_settings.json'
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            # Remove token if it exists
            if 'registry_token' in settings:
                del settings['registry_token']
                
                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
        
        return {
            "success": True,
            "message": "Registry token cleared successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/registry/test-connection")
async def test_registry_connection():
    """Test connection to the registry."""
    try:
        import httpx
        
        settings_file = 'data/registry_settings.json'
        registry_url = "https://registry.mindroot.io"
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                registry_url = settings.get("registry_url", registry_url)
        
        # Test connection to registry
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{registry_url}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                return {
                    "success": True,
                    "message": "Successfully connected to registry.",
                    "data": {
                        "registry_url": registry_url,
                        "stats": stats
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Registry returned status code {response.status_code}",
                    "data": {
                        "registry_url": registry_url,
                        "status_code": response.status_code
                    }
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to connect to registry: {str(e)}",
            "data": {
                "registry_url": registry_url,
                "error": str(e)
            }
        }
