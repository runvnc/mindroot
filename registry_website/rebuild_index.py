#!/usr/bin/env python3
"""
Script to rebuild the vector search index with improved indexing.
Run this after updating the vector_store.py to ensure all existing content
is properly indexed with the new format.
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db, Content
from vector_store import vector_store

def rebuild_vector_index():
    """Rebuild the entire vector index from database content."""
    print("Starting vector index rebuild...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all content from database
        all_content = db.query(Content).all()
        print(f"Found {len(all_content)} items in database")
        
        # Prepare items for vector store
        items = []
        for content in all_content:
            item = {
                'id': str(content.id),
                'title': content.title,
                'description': content.description,
                'metadata': {
                    'title': content.title,
                    'category': content.category,
                    'content_type': content.content_type,
                    'tags': ','.join(content.tags) if isinstance(content.tags, list) else (content.tags or ''),
                    'commands': ','.join(content.commands) if isinstance(content.commands, list) else (content.commands or ''),
                    'services': ','.join(content.services) if isinstance(content.services, list) else (content.services or ''),
                    'owner': content.owner.username if content.owner else 'unknown',
                    'version': content.version
                }
            }
            items.append(item)
        
        # Rebuild the index
        vector_store.rebuild_index(items)
        print(f"Successfully rebuilt vector index with {len(items)} items")
        
        # Test the search
        print("\nTesting search functionality...")
        test_queries = ['test', 'testing', 'exam', 'file', 'data']
        
        for query in test_queries:
            results = vector_store.search(query, n_results=5)
            print(f"\nQuery '{query}': {len(results['results'])} results")
            for i, result in enumerate(results['results'][:3]):
                title = result.get('metadata', {}).get('title', 'Unknown')
                distance = result.get('distance', 'N/A')
                print(f"  {i+1}. {title} (distance: {distance})")
        
    except Exception as e:
        print(f"Error rebuilding index: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_vector_index()
