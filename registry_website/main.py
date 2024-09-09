from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from authentication import Token, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from database import get_db, User, Content
from datetime import timedelta
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Additional imports for running the server
import uvicorn

class ContentCreate(BaseModel):
    title: str
    description: str
    category: str
    content_type: str
    data: dict
    version: str

class ContentResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    content_type: str
    data: dict
    version: str
    owner_id: int

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/publish", response_model=ContentResponse)
def publish_content(content: ContentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_content = db.query(Content).filter(Content.title == content.title, Content.version == content.version).first()
    if existing_content:
        if existing_content.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to update this package.")
        # Update the existing content
        existing_content.description = content.description
        existing_content.category = content.category
        existing_content.content_type = content.content_type
        existing_content.data = content.data
    else:
        # Create a new content
        db_content = Content(**content.dict(), owner_id=current_user.id)
        db.add(db_content)
    db.commit()
    db.refresh(existing_content) if existing_content else db.refresh(db_content)
    return existing_content if existing_content else db_content

@app.get("/search", response_model=List[ContentResponse])
def search_content(query: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(Content).filter(
        (Content.title.contains(query)) |
        (Content.description.contains(query)) |
        (Content.category.contains(query))
    ).all()
    return results

# Code to run the server if the script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
