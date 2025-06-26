from typing import Optional, Dict

async def verify_api_key(api_key: str) -> Optional[Dict]:
    """
    Verify an API key and return user data if valid.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        Dict containing user data if valid, None otherwise
    """
    try:
        # Import here to avoid circular imports
        from mindroot.coreplugins.api_keys.api_key_manager import api_key_manager
        
        key_data = api_key_manager.validate_key(api_key)
        if key_data:
            return {
                'username': key_data['username'],
                'api_key': api_key,
                'created_at': key_data['created_at'],
                'description': key_data.get('description', '')
            }
        return None
    except Exception as e:
        print(f"Error verifying API key: {e}")
        return None
