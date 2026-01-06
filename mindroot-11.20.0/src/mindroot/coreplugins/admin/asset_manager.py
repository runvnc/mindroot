import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import os

class AssetManager:
    """Manages deduplicated asset storage for personas"""
    
    def __init__(self, base_dir: str = "registry_assets"):
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir / "assets"
        self.metadata_dir = self.base_dir / "metadata"
        
        # Create directories
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content bytes"""
        return hashlib.sha256(content).hexdigest()
    
    def store_asset(self, source_path: Path, asset_type: str = "image") -> Tuple[str, bool]:
        """Store an asset and return (hash, was_new)"""
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Calculate hash
        file_hash = self.calculate_file_hash(source_path)
        asset_path = self.assets_dir / file_hash
        
        # Check if asset already exists
        if asset_path.exists():
            # Update reference count
            self._increment_reference_count(file_hash)
            return file_hash, False
        
        # Copy file to assets directory
        shutil.copy2(source_path, asset_path)
        
        # Create metadata
        metadata = {
            "hash": file_hash,
            "type": asset_type,
            "size": source_path.stat().st_size,
            "original_name": source_path.name,
            "reference_count": 1
        }
        
        metadata_path = self.metadata_dir / f"{file_hash}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return file_hash, True
    
    def store_content(self, content: bytes, filename: str, asset_type: str = "image") -> Tuple[str, bool]:
        """Store content bytes and return (hash, was_new)"""
        file_hash = self.calculate_content_hash(content)
        asset_path = self.assets_dir / file_hash
        
        # Check if asset already exists
        if asset_path.exists():
            self._increment_reference_count(file_hash)
            return file_hash, False
        
        # Write content to assets directory
        with open(asset_path, 'wb') as f:
            f.write(content)
        
        # Create metadata
        metadata = {
            "hash": file_hash,
            "type": asset_type,
            "size": len(content),
            "original_name": filename,
            "reference_count": 1
        }
        
        metadata_path = self.metadata_dir / f"{file_hash}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return file_hash, True
    
    def get_asset_path(self, file_hash: str) -> Optional[Path]:
        """Get the path to an asset by hash"""
        asset_path = self.assets_dir / file_hash
        return asset_path if asset_path.exists() else None
    
    def get_asset_metadata(self, file_hash: str) -> Optional[Dict]:
        """Get metadata for an asset"""
        metadata_path = self.metadata_dir / f"{file_hash}.json"
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def _increment_reference_count(self, file_hash: str):
        """Increment reference count for an asset"""
        metadata = self.get_asset_metadata(file_hash)
        if metadata:
            metadata['reference_count'] += 1
            metadata_path = self.metadata_dir / f"{file_hash}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def decrement_reference_count(self, file_hash: str) -> bool:
        """Decrement reference count and delete if zero. Returns True if deleted."""
        metadata = self.get_asset_metadata(file_hash)
        if not metadata:
            return False
        
        metadata['reference_count'] -= 1
        
        if metadata['reference_count'] <= 0:
            # Delete asset and metadata
            asset_path = self.assets_dir / file_hash
            metadata_path = self.metadata_dir / f"{file_hash}.json"
            
            if asset_path.exists():
                asset_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        else:
            # Update metadata
            metadata_path = self.metadata_dir / f"{file_hash}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return False
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        total_assets = len(list(self.assets_dir.glob('*')))
        total_size = sum(f.stat().st_size for f in self.assets_dir.glob('*'))
        
        # Calculate total references
        total_references = 0
        for metadata_file in self.metadata_dir.glob('*.json'):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                total_references += metadata.get('reference_count', 0)
        
        return {
            'total_assets': total_assets,
            'total_size_bytes': total_size,
            'total_references': total_references,
            'deduplication_ratio': total_references / max(total_assets, 1)
        }

# Global asset manager instance
asset_manager = AssetManager()
