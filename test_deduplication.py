#!/usr/bin/env python3
"""
Test script for asset deduplication system
"""

import sys
import os
sys.path.append('/files/mindroot/src')

from mindroot.coreplugins.admin.asset_manager import AssetManager
from pathlib import Path
import tempfile

def test_asset_deduplication():
    """Test the asset deduplication functionality"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize asset manager in temp directory
        asset_manager = AssetManager(temp_dir)
        
        # Create some test image data
        test_image_1 = b"fake_png_data_for_avatar_1"
        test_image_2 = b"fake_png_data_for_avatar_2"
        test_image_1_duplicate = b"fake_png_data_for_avatar_1"  # Same as image 1
        
        print("Testing Asset Deduplication System")
        print("=" * 40)
        
        # Store first image
        hash1, was_new1 = asset_manager.store_content(test_image_1, "avatar1.png", "avatar")
        print(f"Stored image 1: hash={hash1[:8]}..., was_new={was_new1}")
        
        # Store second image (different content)
        hash2, was_new2 = asset_manager.store_content(test_image_2, "avatar2.png", "avatar")
        print(f"Stored image 2: hash={hash2[:8]}..., was_new={was_new2}")
        
        # Store duplicate of first image
        hash3, was_new3 = asset_manager.store_content(test_image_1_duplicate, "avatar1_copy.png", "avatar")
        print(f"Stored duplicate: hash={hash3[:8]}..., was_new={was_new3}")
        
        # Verify deduplication worked
        assert hash1 == hash3, "Duplicate images should have same hash"
        assert was_new1 == True, "First image should be new"
        assert was_new2 == True, "Second image should be new"
        assert was_new3 == False, "Duplicate should not be new"
        
        # Check metadata
        metadata1 = asset_manager.get_asset_metadata(hash1)
        print(f"Image 1 metadata: refs={metadata1['reference_count']}, size={metadata1['size']}")
        
        # Get statistics
        stats = asset_manager.get_stats()
        print(f"\nStorage Statistics:")
        print(f"Total assets: {stats['total_assets']}")
        print(f"Total references: {stats['total_references']}")
        print(f"Deduplication ratio: {stats['deduplication_ratio']:.2f}")
        print(f"Total size: {stats['total_size_bytes']} bytes")
        
        # Test reference counting
        print(f"\nTesting reference counting...")
        deleted = asset_manager.decrement_reference_count(hash1)
        print(f"Decremented hash1, deleted: {deleted}")
        
        metadata1_after = asset_manager.get_asset_metadata(hash1)
        if metadata1_after:
            print(f"Hash1 refs after decrement: {metadata1_after['reference_count']}")
        else:
            print("Hash1 was deleted (no more references)")
        
        print("\n✅ Asset deduplication test completed successfully!")
        
        return {
            'unique_assets': stats['total_assets'],
            'total_references': stats['total_references'],
            'deduplication_ratio': stats['deduplication_ratio']
        }

if __name__ == "__main__":
    try:
        result = test_asset_deduplication()
        print(f"\nTest Results: {result}")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
