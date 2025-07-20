from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import SessionLocal, User
from typing import Optional
import secrets

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username/email and password."""
    db = SessionLocal()
    try:
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
            
        if not verify_password(password, user.password):
            return None
            
        if not user.is_active:
            return None
            
        return user
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_verification_token(email: str) -> str:
    """Create a secure token for email verification."""
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, token: str):
    """Placeholder for sending a verification email."""
    verification_link = f"http://localhost:8000/verify-email/{token}"
    print("\n--- EMAIL VERIFICATION ---")
    print(f"To: {email}")
    print(f"Subject: Verify your email address")
    print(f"Body: Please click the following link to verify your email address:")
    print(verification_link)
    print("--------------------------\n")
    # In a real application, you would use a library like `fastapi-mail`
    # or `smtplib` to send an actual email.
    pass

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """Get current user if token is provided, otherwise return None."""
    if not token:
        return None
    
    try:
        return get_current_user(token)
    except HTTPException:
        return None
