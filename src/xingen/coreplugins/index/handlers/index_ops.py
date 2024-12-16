import json
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from ..models import IndexMetadata
from ..utils import ensure_index_structure
from lib.plugins import load_plugin_manifest
import shutil

async def list_indices(INDEX_DIR: Path):
    """List all available indices"""
    try:
        indices = []
        
        # Check if index directory exists and has content
        if not INDEX_DIR.exists() or not any(INDEX_DIR.glob('*')):
            # If INDEX_DIR exists but is empty, remove it first
            if INDEX_DIR.exists():
                shutil.rmtree(INDEX_DIR)
                
            # Copy default indices
            this_script_path = Path(__file__).parent.parent
            default_indices_path = this_script_path / 'indices'
            shutil.copytree(default_indices_path, INDEX_DIR)

        # List all index directories
        for index_dir in INDEX_DIR.iterdir():
            if index_dir.is_dir():
                index_file = index_dir / 'index.json'
                if index_file.exists():
                    try:
                        with open(index_file, 'r') as f:
                            index_data = json.load(f)
                            manifest = load_plugin_manifest()
                            index_data['installed'] = index_dir.name in manifest.get('indices', {}).get('installed', {})
                            indices.append(index_data)
                    except json.JSONDecodeError:
                        continue  # Skip invalid JSON files

        return JSONResponse({'success': True, 'data': indices})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_index(INDEX_DIR: Path, metadata: IndexMetadata):
    """Create a new index directory with metadata"""
    try:
        index_dir = INDEX_DIR / metadata.name
        if index_dir.exists():
            return JSONResponse({'success': False, 'message': 'Index already exists'})

        # Create index directory structure
        index_dir.mkdir(parents=True)
        ensure_index_structure(index_dir)

        index_data = {
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'url': metadata.url,
            'trusted': metadata.trusted,
            'created_at': datetime.now().isoformat(),
            'plugins': [],
            'agents': []
        }

        with open(index_dir / 'index.json', 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_index(INDEX_DIR: Path, index_name: str, metadata: IndexMetadata):
    """Update index metadata"""
    try:
        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        if not index_file.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(index_file, 'r') as f:
            index_data = json.load(f)

        index_data.update({
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'url': metadata.url,
            'trusted': metadata.trusted,
            'updated_at': datetime.now().isoformat()
        })

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        # If name changed, rename the directory
        if metadata.name != index_name:
            new_index_dir = INDEX_DIR / metadata.name
            index_dir.rename(new_index_dir)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
