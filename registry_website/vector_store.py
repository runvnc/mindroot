import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import json
import os

class RegistryVectorStore:
    def __init__(self, persist_directory: str = "./registry_chroma_db"):
        """Initialize ChromaDB client and collection for registry search."""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collection for MindRoot registry items
        self.collection = self.client.get_or_create_collection(
            name="mindroot_registry",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_item(self, item_id: str, title: str, description: str, metadata: Dict):
        """Add an item to the vector store.
        
        Args:
            item_id: Unique identifier for the item
            title: Item title
            description: Item description
            metadata: Additional metadata (category, tags, etc.)
        """
        # Combine title and description for better search
        search_text = f"{title}. {description}"
        
        # Add tags to search text if available
        if metadata.get('tags'):
            tags_text = " ".join(metadata['tags'])
            search_text += f" Tags: {tags_text}"
        
        # Add commands and services to search text
        if metadata.get('commands'):
            commands_text = " ".join(metadata['commands'])
            search_text += f" Commands: {commands_text}"
            
        if metadata.get('services'):
            services_text = " ".join(metadata['services'])
            search_text += f" Services: {services_text}"
        
        try:
            self.collection.add(
                documents=[search_text],
                metadatas=[metadata],
                ids=[item_id]
            )
        except Exception as e:
            print(f"Error adding item {item_id} to vector store: {e}")
    
    def update_item(self, item_id: str, title: str, description: str, metadata: Dict):
        """Update an existing item in the vector store."""
        try:
            # Delete the old entry
            self.collection.delete(ids=[item_id])
            # Add the updated entry
            self.add_item(item_id, title, description, metadata)
        except Exception as e:
            print(f"Error updating item {item_id} in vector store: {e}")
    
    def delete_item(self, item_id: str):
        """Delete an item from the vector store."""
        try:
            self.collection.delete(ids=[item_id])
        except Exception as e:
            print(f"Error deleting item {item_id} from vector store: {e}")
    
    def search(self, query: str, n_results: int = 20, filter_dict: Optional[Dict] = None) -> Dict:
        """Search for items using semantic similarity.
        
        Args:
            query: Search query
            n_results: Maximum number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            Dictionary with search results
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_dict
            )
            
            # Format results for easier consumption
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, item_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': item_id,
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'document': results['documents'][0][i] if results['documents'] else ""
                    })
            
            return {
                'results': formatted_results,
                'total': len(formatted_results)
            }
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return {'results': [], 'total': 0}
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                'total_items': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {'total_items': 0, 'collection_name': 'unknown'}
    
    def rebuild_index(self, items: List[Dict]):
        """Rebuild the entire index from a list of items.
        
        Args:
            items: List of dictionaries with 'id', 'title', 'description', and 'metadata'
        """
        try:
            # Clear existing collection
            self.client.delete_collection("mindroot_registry")
            
            # Recreate collection
            self.collection = self.client.get_or_create_collection(
                name="mindroot_registry",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Add all items
            for item in items:
                self.add_item(
                    item['id'],
                    item['title'],
                    item['description'],
                    item['metadata']
                )
                
            print(f"Rebuilt index with {len(items)} items")
        except Exception as e:
            print(f"Error rebuilding index: {e}")

# Global instance
vector_store = RegistryVectorStore()
