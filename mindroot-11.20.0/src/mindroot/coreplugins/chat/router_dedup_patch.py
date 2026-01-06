# Patch for chat router to add deduplication support
# This should be integrated into the main router.py file

# Add this code to the get_persona_avatar function after line 59:

# Check if this is a registry persona with deduplicated assets
if persona_path.startswith('registry/'):
    persona_json_path = f"personas/{persona_path}/persona.json"
    if os.path.exists(persona_json_path):
        try:
            with open(persona_json_path, 'r') as f:
                persona_data = json.load(f)
            
            # Check if persona has asset hashes (deduplicated storage)
            asset_hashes = persona_data.get('asset_hashes', {})
            if 'avatar' in asset_hashes:
                # Redirect to deduplicated asset endpoint
                return RedirectResponse(f"/assets/{asset_hashes['avatar']}")
        except Exception as e:
            print(f"Error checking for deduplicated assets: {e}")
