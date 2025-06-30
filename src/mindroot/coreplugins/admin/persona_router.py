from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pathlib import Path
import json
import shutil
import traceback
from .asset_manager import asset_manager

router = APIRouter()

BASE_DIR = Path('personas')
local_dir = BASE_DIR / "local"
shared_dir = BASE_DIR / "shared"
local_dir.mkdir(parents=True, exist_ok=True)
shared_dir.mkdir(parents=True, exist_ok=True)

# Registry directory for namespaced personas
registry_dir = BASE_DIR / "registry"
registry_dir.mkdir(parents=True, exist_ok=True)

@router.get('/personas/{scope}/{name}')
def read_persona(scope: str, name: str):
    if scope not in ['local', 'shared', 'registry']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    persona_path = BASE_DIR / scope / name / 'persona.json'
    if not persona_path.exists():
        raise HTTPException(status_code=404, detail='Persona not found')
    with open(persona_path, 'r') as f:
        persona = json.load(f)
    if 'moderated' not in persona:
        persona['moderated'] = False
    return persona


@router.get('/personas/{scope}')
def list_personas(scope: str):
    if scope not in ['local', 'shared', 'registry']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    scope_dir = BASE_DIR / scope
    personas = [p.name for p in scope_dir.iterdir() if p.is_dir()]
    print(f"Read personas from dir {scope_dir}: {personas}")
    return [{'name': name} for name in personas]

@router.get('/personas/{persona_path:path}')
def read_persona_by_path(persona_path: str):
    """Read persona by full path (supports registry/owner/name format)"""
    try:
        # Handle registry personas: registry/owner/name
        if persona_path.startswith('registry/'):
            full_path = BASE_DIR / persona_path / 'persona.json'
        else:
            # Handle simple names: check local first, then shared
            full_path = BASE_DIR / 'local' / persona_path / 'persona.json'
            if not full_path.exists():
                full_path = BASE_DIR / 'shared' / persona_path / 'persona.json'
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail='Persona not found')
            
        with open(full_path, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Persona not found: {str(e)}')

@router.post('/personas/registry')
def create_registry_persona(persona: str = Form(...), owner: str = Form(...)):
    """Create a registry persona with owner namespace"""
    try:
        persona_data = json.loads(persona)
        persona_name = persona_data.get('name')
        
        if not persona_name:
            raise HTTPException(status_code=400, detail='Persona name is required')
        if not owner:
            raise HTTPException(status_code=400, detail='Owner is required for registry personas')
        
        # Create registry persona path: personas/registry/owner/name/
        persona_path = BASE_DIR / 'registry' / owner / persona_name / 'persona.json'
        
        if persona_path.exists():
            # Update existing persona instead of failing
            print(f"Updating existing registry persona: {owner}/{persona_name}")
        
        persona_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(persona_path, 'w') as f:
            json.dump(persona_data, f, indent=2)
            
        return {'status': 'success', 'path': f'registry/{owner}/{persona_name}'}
        
    except Exception as e:
        print(f"Error creating registry persona: {e}")
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

@router.post('/personas/registry/with-assets')
def create_registry_persona_with_assets(persona: str = Form(...), owner: str = Form(...), 
                                       faceref: UploadFile = File(None), avatar: UploadFile = File(None)):
    """Create a registry persona with deduplicated asset storage"""
    try:
        print(f"Received persona data (first 200 chars): {persona[:200]}...")
        print(f"Received owner: {owner}")
        print(f"Received faceref: {faceref.filename if faceref else 'None'}")
        print(f"Received avatar: {avatar.filename if avatar else 'None'}")
        
        persona_data = json.loads(persona)
        persona_name = persona_data.get('name')
        
        if not persona_name:
            raise HTTPException(status_code=400, detail='Persona name is required')
        if not owner:
            raise HTTPException(status_code=400, detail='Owner is required for registry personas')
        
        # Store assets with deduplication
        asset_hashes = {}
        
        if faceref:
            content = faceref.file.read()
            file_hash, was_new = asset_manager.store_content(content, faceref.filename, "faceref")
            asset_hashes['faceref'] = file_hash
            
        if avatar:
            content = avatar.file.read()
            file_hash, was_new = asset_manager.store_content(content, avatar.filename, "avatar")
            asset_hashes['avatar'] = file_hash
        
        # Add asset references to persona data
        persona_data['asset_hashes'] = asset_hashes
        
        # For registry personas, update the name to include the owner namespace
        # This ensures the chat UI can find the images at the correct path
        if 'name' in persona_data:
            persona_data['name'] = f"{owner}/{persona_name}"
        
        # Create registry persona path first
        persona_path = BASE_DIR / 'registry' / owner / persona_name / 'persona.json'
        persona_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ALSO copy assets to traditional locations for compatibility
        if faceref:
            faceref_path = persona_path.parent / 'faceref.png'
            faceref_path.parent.mkdir(parents=True, exist_ok=True)
            with open(faceref_path, 'wb') as f:
                faceref.file.seek(0)  # Reset file pointer
                f.write(faceref.file.read())
                
        if avatar:
            avatar_path = persona_path.parent / 'avatar.png'
            avatar_path.parent.mkdir(parents=True, exist_ok=True)
            with open(avatar_path, 'wb') as f:
                avatar.file.seek(0)  # Reset file pointer
                f.write(avatar.file.read())
        
        with open(persona_path, 'w') as f:
            json.dump(persona_data, f, indent=2)
            
        return {
            'status': 'success', 
            'path': f'registry/{owner}/{persona_name}',
            'asset_hashes': asset_hashes
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Invalid JSON received: {persona}")
        raise HTTPException(status_code=400, detail=f'Invalid JSON in persona data: {str(e)}')
    except Exception as e:
        print(f"Error creating registry persona with assets: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

@router.get('/assets/{asset_hash}')
def serve_asset(asset_hash: str):
    """Serve a deduplicated asset by hash"""
    try:
        asset_path = asset_manager.get_asset_path(asset_hash)
        if not asset_path:
            raise HTTPException(status_code=404, detail='Asset not found')
        
        metadata = asset_manager.get_asset_metadata(asset_hash)
        
        with open(asset_path, 'rb') as f:
            content = f.read()
        
        # Determine content type based on metadata
        content_type = "image/png" if metadata and metadata.get('type') in ['avatar', 'faceref'] else "application/octet-stream"
        
        return Response(content=content, media_type=content_type)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Asset not found: {str(e)}')

@router.post('/personas/{scope}')
def create_persona(scope: str, persona: str = Form(...), faceref: UploadFile = File(None), avatar: UploadFile = File(None)):
    try:
        print("In create_persona")
        print("scope is ", scope)
        persona = json.loads(persona)

        print("persona is ", persona)

        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
        persona_name = persona.get('name')
        if not persona_name:
            raise HTTPException(status_code=400, detail='Persona name is required')
        persona_path = BASE_DIR / scope / persona_name / 'persona.json'
        if persona_path.exists():
            raise HTTPException(status_code=400, detail='Persona already exists')
        persona_path.parent.mkdir(parents=True, exist_ok=True)

        target_dir = Path(__file__).resolve().parent.parent / 'static/personas' / persona_name

        target_dir.mkdir(parents=True, exist_ok=True)
        print('\033[93m' + str(target_dir) + '\033[0m')
        if faceref:
            print("Trying to save faceref")
            faceref_path = persona_path.parent / 'faceref.png'
            print("faceref path is ", faceref_path)
            with open(faceref_path, 'wb') as f:
                print("opened file for writing")
                f.write(faceref.file.read())
            # Copy faceref to new location
            new_faceref_path = target_dir / 'faceref.png'
            shutil.copy2(faceref_path, new_faceref_path)
            persona['faceref'] = str(new_faceref_path)

        if avatar:
            print("Trying to save avatar")
            avatar_path = persona_path.parent / 'avatar.png'
            with open(avatar_path, 'wb') as f:
                print("opened file for writing")
                f.write(avatar.file.read())
            # Copy avatar to new location
            new_avatar_path = target_dir / 'avatar.png'
            shutil.copy2(avatar_path, new_avatar_path)
            persona['avatar'] = str(new_avatar_path)

        with open(persona_path, 'w') as f:
            json.dump(persona, f, indent=2)
        return {'status': 'success'}

    except Exception as e:
        print("Error in create_persona")
        raise HTTPException(status_code=500, detail='Internal server error ' + str(e))

@router.put('/personas/{scope}/{name}')
def update_persona(scope: str, name:str, persona: str = Form(...), faceref: UploadFile = File(None), avatar: UploadFile = File(None)):
     
    try:
        print("In update_persona")
        print("scope is ", scope)
        print("name is ", name)
        print("BASE_DIR is ", BASE_DIR)
        persona = json.loads(persona)
        persona_name = persona.get('name')

        print("persona is ", persona)
        
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
        persona_path = BASE_DIR / scope / name / 'persona.json'
        if not persona_path.exists():
            raise HTTPException(status_code=404, detail='Persona not found')
        if 'moderated' not in persona:
            persona['moderated'] = False
        
        target_dir = Path(__file__).resolve().parent.parent / 'static/personas' / persona_name

        target_dir.mkdir(parents=True, exist_ok=True)
        print('\033[93m' + str(BASE_DIR) + '\033[0m')
        print('\033[93m' + str(target_dir) + '\033[0m')
 
        if faceref:
            print("Trying to save faceref")
            faceref_path = persona_path.parent / 'faceref.png'
            print("faceref path is ", faceref_path)
            with open(faceref_path, 'wb') as f:
                print("opened file for writing")
                f.write(faceref.file.read())
            # Copy faceref to new location
            new_faceref_path = target_dir / 'faceref.png'
            shutil.copy2(faceref_path, new_faceref_path)
            persona['faceref'] = str(new_faceref_path)
        
        if avatar:
            print("Trying to save avatar")
            avatar_path = persona_path.parent / 'avatar.png'
            with open(avatar_path, 'wb') as f:
                print("opened file for writing")
                f.write(avatar.file.read())
            # Copy avatar to new location
            new_avatar_path = target_dir / 'avatar.png'
            shutil.copy2(avatar_path, new_avatar_path)
            persona['avatar'] = str(new_avatar_path)
 
        with open(persona_path, 'w') as f:
            json.dump(persona, f, indent=2)
        return {'status': 'success'}
    except Exception as e:
        print("Error in update_persona")
        print(str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail='Internal server error '+ str(e))

