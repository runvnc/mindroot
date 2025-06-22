#!/usr/bin/env python3
"""
MindRoot Registry Startup Script

This script initializes and starts the MindRoot registry server.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import chromadb
        import sqlalchemy
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def initialize_database():
    """Initialize the database with tables."""
    try:
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def create_admin_user():
    """Create a default admin user if it doesn't exist."""
    try:
        from database import SessionLocal, User
        from authentication import get_password_hash
        
        db = SessionLocal()
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@mindroot.local",
                password=get_password_hash("admin123"),
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✓ Admin user created (username: admin, password: admin123)")
        else:
            print("✓ Admin user already exists")
            
        db.close()
        return True
    except Exception as e:
        print(f"✗ Admin user creation failed: {e}")
        return False

def initialize_vector_store():
    """Initialize the ChromaDB vector store."""
    try:
        from vector_store import vector_store
        stats = vector_store.get_collection_stats()
        print(f"✓ Vector store initialized ({stats['total_items']} items)")
        return True
    except Exception as e:
        print(f"✗ Vector store initialization failed: {e}")
        return False

def start_server(host="0.0.0.0", port=8000):
    """Start the FastAPI server."""
    try:
        import uvicorn
        from main import app
        
        print(f"🚀 Starting MindRoot Registry on http://{host}:{port}")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🌐 Web Interface: http://localhost:8000")
        print("\nPress Ctrl+C to stop the server")
        
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 Registry server stopped")
    except Exception as e:
        print(f"✗ Server startup failed: {e}")
        return False

def main():
    """Main startup routine."""
    print("🧠 MindRoot Registry Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Create admin user
    if not create_admin_user():
        sys.exit(1)
    
    # Initialize vector store
    if not initialize_vector_store():
        sys.exit(1)
    
    print("\n✅ Registry initialization complete!")
    print("\nDefault admin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nPlease change the admin password after first login.")
    print("=" * 40)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
