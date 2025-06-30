import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import os
from sqlalchemy.orm import Session
from database import Asset, ContentAsset, get_db

class RegistryAssetManager:
    """Manages deduplicated asset storage for the registry website"""
    
    def __init__(self, base_dir: str = "registry_assets"):
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir / "assets"
        
        # Create directories
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content bytes"""
        return hashlib.sha256(content).hexdigest()
    
    def store_asset(self, content: bytes, content_type: str, asset_type: str = "image") -> Tuple[str, bool]:
        """Store an asset and return (hash, was_new)"""
        file_hash = self.calculate_content_hash(content)
        asset_path = self.assets_dir / file_hash
        
        # Get database session
        db = next(get_db())
        
        try:
            # Check if asset already exists in database
            existing_asset = db.query(Asset).filter(Asset.hash == file_hash).first()
            
            if existing_asset:
                # Update reference count
                existing_asset.reference_count += 1
                db.commit()
                return file_hash, False
            
            # Write content to assets directory if not exists
            if not asset_path.exists():
                with open(asset_path, 'wb') as f:
                    f.write(content)
            
            # Create database record
            new_asset = Asset(
                hash=file_hash,
                content_type=content_type,
                size=len(content),
                reference_count=1
            )
            
            db.add(new_asset)
            db.commit()
            
            return file_hash, True
            
        finally:
            db.close()
    
    def get_asset_path(self, file_hash: str) -> Optional[Path]:
        """Get the path to an asset by hash"""
        asset_path = self.assets_dir / file_hash
        return asset_path if asset_path.exists() else None
    
    def get_asset_metadata(self, file_hash: str) -> Optional[Dict]:
        """Get metadata for an asset from database"""
        db = next(get_db())
        
        try:
            asset = db.query(Asset).filter(Asset.hash == file_hash).first()
            if not asset:
                return None
            
            return {
                "hash": asset.hash,
                "content_type": asset.content_type,
                "size": asset.size,
                "reference_count": asset.reference_count,
                "created_at": asset.created_at.isoformat()
            }
        finally:
            db.close()
    
    def link_asset_to_content(self, content_id: int, asset_hash: str, asset_type: str):
        """Link an asset to content"""
        db = next(get_db())
        
        try:
            # Get asset by hash
            asset = db.query(Asset).filter(Asset.hash == asset_hash).first()
            if not asset:
                raise ValueError(f"Asset with hash {asset_hash} not found")
            
            # Check if link already exists
            existing_link = db.query(ContentAsset).filter(
                ContentAsset.content_id == content_id,
                ContentAsset.asset_id == asset.id,
                ContentAsset.asset_type == asset_type
            ).first()
            
            if not existing_link:
                # Create new link
                content_asset = ContentAsset(
                    content_id=content_id,
                    asset_id=asset.id,
                    asset_type=asset_type
                )
                db.add(content_asset)
                db.commit()
                
        finally:
            db.close()
    
    def decrement_reference_count(self, file_hash: str) -> bool:
        """Decrement reference count and delete if zero. Returns True if deleted."""
        db = next(get_db())
        
        try:
            asset = db.query(Asset).filter(Asset.hash == file_hash).first()
            if not asset:
                return False
            
            asset.reference_count -= 1
            
            if asset.reference_count <= 0:
                # Delete asset file and database record
                asset_path = self.assets_dir / file_hash
                if asset_path.exists():
                    asset_path.unlink()
                
                # Delete content asset links
                db.query(ContentAsset).filter(ContentAsset.asset_id == asset.id).delete()
                
                # Delete asset record
                db.delete(asset)
                db.commit()
                
                return True
            else:
                db.commit()
                return False
                
        finally:
            db.close()
    
    def get_content_assets(self, content_id: int) -> Dict[str, str]:
        """Get all asset hashes for a content item"""
        db = next(get_db())
        
        try:
            content_assets = db.query(ContentAsset).filter(
                ContentAsset.content_id == content_id
            ).all()
            
            result = {}
            for ca in content_assets:
                asset = db.query(Asset).filter(Asset.id == ca.asset_id).first()
                if asset:
                    result[ca.asset_type] = asset.hash
            
            return result
            
        finally:
            db.close()
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        db = next(get_db())
        
        try:
            total_assets = db.query(Asset).count()
            total_size = db.query(Asset).with_entities(Asset.size).all()
            total_size_bytes = sum(size[0] for size in total_size if size[0])
            
            total_references = db.query(Asset).with_entities(Asset.reference_count).all()
            total_ref_count = sum(ref[0] for ref in total_references if ref[0])
            
            return {
                'total_assets': total_assets,
                'total_size_bytes': total_size_bytes,
                'total_references': total_ref_count,
                'deduplication_ratio': total_ref_count / max(total_assets, 1)
            }
            
        finally:
            db.close()

# Global asset manager instance
registry_asset_manager = RegistryAssetManager()
