from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from authentication import Token, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, get_password_hash, create_verification_token
from database import get_db, User, Content, Rating, InstallLog
from vector_store import vector_store
from asset_manager import registry_asset_manager
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
from email_sender import send_verification_email
import uvicorn
import os
from pathlib import Path
import base64
import hashlib

app = FastAPI(
    title="MindRoot Registry",
    description="Registry for MindRoot plugins and agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static and templates directories if they don't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

# Mount static files and templates only if directories exist
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

if templates_dir.exists():
    templates = Jinja2Templates(directory="templates")
else:
    templates = None

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

class ContentCreate(BaseModel):
    title: str
    description: str
    category: str
    content_type: str
    data: dict
    version: str
    github_url: Optional[str] = None
    pypi_module: Optional[str] = None
    commands: Optional[List[str]] = []
    services: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    dependencies: Optional[List[str]] = []

class ContentResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    content_type: str
    data: dict
    version: str
    github_url: Optional[str]
    pypi_module: Optional[str]
    commands: Optional[List[str]]
    services: Optional[List[str]]
    tags: Optional[List[str]]
    dependencies: Optional[List[str]]
    download_count: int
    install_count: int
    rating: float
    rating_count: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

class RatingCreate(BaseModel):
    content_id: int
    rating: int
    review: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[ContentResponse]
    total: int
    semantic_results: Optional[List[dict]] = None

# Root endpoint with fallback HTML
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse('''
<!DOCTYPE html>
<html>
<head>
    <title>MindRoot Registry</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }
        h1 { color: #333; }
        .api-link { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 MindRoot Registry</h1>
        <p>Welcome to the MindRoot Plugin and Agent Registry</p>
        <p><a href="/docs" class="api-link">View API Documentation</a></p>
        <h2>Quick Stats</h2>
        <p>Visit <a href="/stats">/stats</a> for registry statistics</p>
    </div>
</body>
</html>
        ''')

# Authentication endpoints
@app.post("/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    verification_token = create_verification_token(user_data.email)
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        is_active=False, # User is inactive until email is verified
        email_verification_token=verification_token
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    await send_verification_email(user_data.email, verification_token)
    
    return {"message": "Registration successful. Please check your email to verify your account."}

@app.get("/verify-email/{token}", response_class=HTMLResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    user.email_verified = True
    user.is_active = True
    user.email_verification_token = None
    db.commit()
    
    return HTMLResponse("<h1>Email verified successfully!</h1><p>You can now log in.</p>")

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your inbox for a verification link."
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

@app.get("/assets/{asset_hash}")
def serve_asset(asset_hash: str):
    """Serve a deduplicated asset by hash"""
    try:
        asset_path = registry_asset_manager.get_asset_path(asset_hash)
        if not asset_path:
            raise HTTPException(status_code=404, detail='Asset not found')
        
        metadata = registry_asset_manager.get_asset_metadata(asset_hash)
        
        with open(asset_path, 'rb') as f:
            content = f.read()
        
        # Determine content type from metadata
        content_type = metadata.get('content_type', 'application/octet-stream') if metadata else 'application/octet-stream'
        
        from fastapi.responses import Response
        return Response(content=content, media_type=content_type)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Asset not found: {str(e)}')

def extract_and_store_assets(data: dict, content_id: int) -> dict:
    """Extract base64 assets from data and store them deduplicated"""
    if not isinstance(data, dict):
        return data
    
    # Look for persona_assets in the data
    if 'persona_assets' in data:
        persona_assets = data['persona_assets']
        asset_hashes = {}
        
        for asset_type, asset_data in persona_assets.items():
            if isinstance(asset_data, dict) and 'data' in asset_data:
                # Decode base64 data
                try:
                    content = base64.b64decode(asset_data['data'])
                    content_type = asset_data.get('type', 'image/png')
                    
                    # Store asset
                    asset_hash, was_new = registry_asset_manager.store_asset(content, content_type, asset_type)
                    
                    # Link to content
                    registry_asset_manager.link_asset_to_content(content_id, asset_hash, asset_type)
                    
                    asset_hashes[asset_type] = asset_hash
                    
                except Exception as e:
                    print(f"Error processing asset {asset_type}: {e}")
        
        # Replace persona_assets with asset_hashes in the data
        if asset_hashes:
            # Remove the large base64 data and replace with hashes
            data_copy = data.copy()
            if 'persona_data' in data_copy:
                data_copy['persona_data'] = data_copy['persona_data'].copy()
                data_copy['persona_data']['asset_hashes'] = asset_hashes
                # Remove the large persona_assets to save space
                data_copy['persona_data'].pop('persona_assets', None)
            data_copy.pop('persona_assets', None)
            return data_copy
   
    return data

# Content management endpoints
@app.post("/publish", response_model=ContentResponse)
def publish_content(
    content: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_content = db.query(Content).filter(
        Content.title == content.title,
        Content.version == content.version
    ).first()
    
    if existing_content:
        if existing_content.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update this package."
            )
        
        for field, value in content.dict().items():
            setattr(existing_content, field, value)
        existing_content.updated_at = datetime.utcnow()
        
        # Extract and store assets
        existing_content.data = extract_and_store_assets(existing_content.data, existing_content.id)
        
        db.commit()
        db.refresh(existing_content)
        
        vector_store.update_item(
            str(existing_content.id),
            existing_content.title,
            existing_content.description,
            {
                'title': existing_content.title,
                'category': existing_content.category,
                'content_type': existing_content.content_type,
                'tags': ','.join(existing_content.tags) if isinstance(existing_content.tags, list) else (existing_content.tags or ''),
                'commands': ','.join(existing_content.commands) if isinstance(existing_content.commands, list) else (existing_content.commands or ''),
                'services': ','.join(existing_content.services) if isinstance(existing_content.services, list) else (existing_content.services or ''),
                'owner': current_user.username,
                'version': existing_content.version
            }
        )
        
        return existing_content
    else:
        db_content = Content(
            **content.dict(),
            owner_id=current_user.id
        )
        
        db.add(db_content)
        db.commit()
        db.refresh(db_content)
        
        # Extract and store assets after getting the content ID
        db_content.data = extract_and_store_assets(db_content.data, db_content.id)
        db.commit()
        
        vector_store.add_item(
            str(db_content.id),
            db_content.title,
            db_content.description,
            {
                'title': db_content.title,
                'category': db_content.category,
                'content_type': db_content.content_type,
                'tags': ','.join(db_content.tags) if isinstance(db_content.tags, list) else (db_content.tags or ''),
                'commands': ','.join(db_content.commands) if isinstance(db_content.commands, list) else (db_content.commands or ''),
                'services': ','.join(db_content.services) if isinstance(db_content.services, list) else (db_content.services or ''),
                'owner': current_user.username,
                'version': db_content.version
            }
        )
        
        return db_content

@app.get("/search", response_model=SearchResponse)
def search_content(
    query: str,
    category: Optional[str] = None,
    limit: int = 20,
    semantic: bool = True,
    sort: Optional[str] = None,
    db: Session = Depends(get_db)
):
    print(f"\n=== SEARCH DEBUG ===")
    print(f"Query: '{query}'")
    print(f"Category: {category}")
    print(f"Semantic: {semantic}")
    print(f"Sort: {sort}")
    
    db_query = db.query(Content)
    
    if category:
        db_query = db_query.filter(Content.category == category)
    
    # Only apply text filters if query is not empty
    if query.strip():
        db_query = db_query.filter(
            (Content.title.contains(query)) |
            (Content.description.contains(query))
        )
    
    # Apply sorting
    if sort == "downloads":
        db_query = db_query.order_by(Content.download_count.desc())
    else:
        db_query = db_query.order_by(Content.created_at.desc())
    
    db_results = db_query.limit(limit).all()
    print(f"SQL Results: {len(db_results)} items")
    
    semantic_results = None
    if semantic:
        filter_dict = {"category": category} if category else None
        # Use a broader search if query is empty or very short
        search_query = query if query.strip() else "*"
        if len(query.strip()) < 3:
            # For short queries, search more broadly
            search_query = f"{query} plugin agent tool"
        semantic_results = vector_store.search(search_query, n_results=limit, filter_dict=filter_dict)['results']
    
    print(f"Semantic Results: {len(semantic_results) if semantic_results else 0} items")
    if semantic_results:
        print("Top 10 semantic results:")
        for i, result in enumerate(semantic_results[:10]):
            print(f"  {i+1}. ID: {result['id']}, Distance: {result.get('distance', 'N/A'):.4f}, Title: {result.get('metadata', {}).get('title', 'N/A')}")
    
    return {
        "results": db_results,
        "total": len(db_results),
        "semantic_results": semantic_results
    }

@app.get("/content/{content_id}", response_model=ContentResponse)
def get_content(content_id: int, db: Session = Depends(get_db)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

@app.post("/install/{content_id}")
def track_install(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    install_log = InstallLog(
        content_id=content_id,
        user_id=None,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "")
    )
    
    db.add(install_log)
    content.install_count += 1
    db.commit()
    
    return {"success": True, "message": "Install tracked"}

@app.get("/stats")
def get_registry_stats(db: Session = Depends(get_db)):
    total_content = db.query(Content).count()
    total_plugins = db.query(Content).filter(Content.category == "plugin").count()
    total_agents = db.query(Content).filter(Content.category == "agent").count()
    total_users = db.query(User).count()
    total_installs = db.query(InstallLog).count()
    
    vector_stats = vector_store.get_collection_stats()
    
    return {
        "total_content": total_content,
        "total_plugins": total_plugins,
        "total_agents": total_agents,
        "total_users": total_users,
        "total_installs": total_installs,
        "vector_store": vector_stats
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
