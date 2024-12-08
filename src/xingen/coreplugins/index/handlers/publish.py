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
        zip_url = f"/index/published/{zip_filename}"

        return JSONResponse({
            'success': True,
            'message': 'Index published successfully',
            'zip_file': zip_url
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish index: {str(e)}")
