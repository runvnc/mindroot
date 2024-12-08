import os
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from ..utils import install_persona

async def publish_index(INDEX_DIR: Path, PUBLISHED_DIR: Path, index_name: str):
    """Publish an index by creating a zip file containing index.json and persona directories."""
    try:
        index_dir = INDEX_DIR / index_name
        if not index_dir.exists() or not index_dir.is_dir():
            raise HTTPException(status_code=404, detail="Index directory not found")

        # Create a timestamp for the zip file name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"{index_name}-{timestamp}.zip"
        zip_path = PUBLISHED_DIR / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add index.json
            index_json_path = index_dir / 'index.json'
            if index_json_path.exists():
                zipf.write(index_json_path, 'index.json')

            # Add persona directories if they exist
            personas_dir = index_dir / 'personas'
            if personas_dir.exists():
                for persona_dir in personas_dir.iterdir():
                    if persona_dir.is_dir():
                        # Add all files from the persona directory
                        for root, _, files in os.walk(persona_dir):
                            for file in files:
                                file_path = Path(root) / file
                                # Create relative path for the zip file
                                arc_name = f"personas/{persona_dir.name}/{file}"
                                zipf.write(file_path, arc_name)

        # Return URL path that can be used with the static file handler
        zip_url = f"/published/{zip_filename}"

        return JSONResponse({
            'success': True,
            'message': 'Index published successfully',
            'zip_file': zip_url
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish index: {str(e)}")

async def install_index_from_zip(INDEX_DIR: Path, file: UploadFile):
    """Install an index from a zip file."""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a zip archive")

    # Create temporary directory for processing
    temp_dir = Path("temp_index_install")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Save uploaded file
        zip_path = temp_dir / file.filename
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        # Extract zip contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Look for index.json in the extracted contents
        index_files = list(temp_dir.rglob('index.json'))
        if not index_files:
            raise HTTPException(status_code=400, detail="No index.json found in zip file")

        # Read the index metadata
        with open(index_files[0], 'r') as f:
            index_data = json.load(f)

        index_name = index_data.get('name')
        if not index_name:
            raise HTTPException(status_code=400, detail="Invalid index.json: missing name field")

        # Process agents and their personas
        index_root = index_files[0].parent
        personas_dir = index_root / 'personas'
        if personas_dir.exists():
            for persona_dir in personas_dir.iterdir():
                if persona_dir.is_dir():
                    persona_name = persona_dir.name
                    # Install persona to the correct location
                    install_persona(persona_dir, persona_name)

        # Move index to final location
        target_dir = INDEX_DIR / index_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        # Create new index directory with index.json
        target_dir.mkdir(parents=True)
        shutil.copy2(index_files[0], target_dir / 'index.json')

        # Copy personas directory if it exists
        if personas_dir.exists():
            shutil.copytree(personas_dir, target_dir / 'personas', dirs_exist_ok=True)

        return JSONResponse({
            'success': True,
            'message': f"Index '{index_name}' installed successfully"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install index: {str(e)}")
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
