from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from authentication import Token, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, get_password_hash
from database import get_db, User, Content, Rating, InstallLog
from vector_store import vector_store
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
import uvicorn

app = FastAPI(
    title="MindRoot Registry",
    description="Registry for MindRoot plugins and agents",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    category: str  # 'plugin' or 'agent'
    content_type: str  # 'mindroot_plugin' or 'mindroot_agent'
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
    rating: int  # 1-5
    review: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[ContentResponse]
    total: int
    semantic_results: Optional[List[dict]] = None

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Simple landing page for the registry."""
    return templates.TemplateResponse("index.html", {"request": request})

# Authentication endpoints
@app.post("/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Content management endpoints
@app.post("/publish", response_model=ContentResponse)
def publish_content(
    content: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish a new plugin or agent to the registry."""
    # Check if content with same title and version already exists
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
        
        # Update existing content
        for field, value in content.dict().items():
            setattr(existing_content, field, value)
        existing_content.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_content)
        
        # Update vector store
        vector_store.update_item(
            str(existing_content.id),
            existing_content.title,
            existing_content.description,
            {
                'category': existing_content.category,
                'content_type': existing_content.content_type,
                'tags': existing_content.tags or [],
                'commands': existing_content.commands or [],
                'services': existing_content.services or [],
                'owner': current_user.username,
                'version': existing_content.version
            }
        )
        
        return existing_content
    else:
        # Create new content
        db_content = Content(
            **content.dict(),
            owner_id=current_user.id
        )
        
        db.add(db_content)
        db.commit()
        db.refresh(db_content)
        
        # Add to vector store
        vector_store.add_item(
            str(db_content.id),
            db_content.title,
            db_content.description,
            {
                'category': db_content.category,
                'content_type': db_content.content_type,
                'tags': db_content.tags or [],
                'commands': db_content.commands or [],
                'services': db_content.services or [],
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
    db: Session = Depends(get_db)
):
    """Search for content using both database and semantic search."""
    # Database search
    db_query = db.query(Content)
    
    if category:
        db_query = db_query.filter(Content.category == category)
    
    # Text search in title and description
    db_query = db_query.filter(
        (Content.title.contains(query)) |
        (Content.description.contains(query))
    )
    
    db_results = db_query.limit(limit).all()
    
    # Semantic search if enabled
    semantic_results = None
    if semantic:
        filter_dict = {"category": category} if category else None
        semantic_results = vector_store.search(query, n_results=limit, filter_dict=filter_dict)
    
    return {
        "results": db_results,
        "total": len(db_results),
        "semantic_results": semantic_results
    }

@app.get("/content/{content_id}", response_model=ContentResponse)
def get_content(content_id: int, db: Session = Depends(get_db)):
    """Get specific content by ID."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

@app.post("/install/{content_id}")
def track_install(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Track an installation of content."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Create install log
    install_log = InstallLog(
        content_id=content_id,
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )
    
    db.add(install_log)
    
    # Increment install count
    content.install_count += 1
    
    db.commit()
    
    return {"success": True, "message": "Install tracked"}

@app.post("/rate")
def rate_content(
    rating_data: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rate content."""
    if rating_data.rating < 1 or rating_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Check if user already rated this content
    existing_rating = db.query(Rating).filter(
        Rating.content_id == rating_data.content_id,
        Rating.user_id == current_user.id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        existing_rating.review = rating_data.review
    else:
        # Create new rating
        new_rating = Rating(
            content_id=rating_data.content_id,
            user_id=current_user.id,
            rating=rating_data.rating,
            review=rating_data.review
        )
        db.add(new_rating)
    
    # Update content rating statistics
    content = db.query(Content).filter(Content.id == rating_data.content_id).first()
    if content:
        ratings = db.query(Rating).filter(Rating.content_id == rating_data.content_id).all()
        content.rating = sum(r.rating for r in ratings) / len(ratings)
        content.rating_count = len(ratings)
    
    db.commit()
    
    return {"success": True, "message": "Rating submitted"}

@app.get("/stats")
def get_registry_stats(db: Session = Depends(get_db)):
    """Get registry statistics."""
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

# Admin endpoints
@app.post("/admin/rebuild-index")
def rebuild_vector_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rebuild the vector search index (admin only)."""
    # Simple admin check - in production, implement proper role-based access
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all content
    all_content = db.query(Content).all()
    
    # Prepare items for indexing
    items = []
    for content in all_content:
        items.append({
            'id': str(content.id),
            'title': content.title,
            'description': content.description,
            'metadata': {
                'category': content.category,
                'content_type': content.content_type,
                'tags': content.tags or [],
                'commands': content.commands or [],
                'services': content.services or [],
                'owner': content.owner.username,
                'version': content.version
            }
        })
    
    # Rebuild index
    vector_store.rebuild_index(items)
    
    return {"success": True, "message": f"Index rebuilt with {len(items)} items"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
