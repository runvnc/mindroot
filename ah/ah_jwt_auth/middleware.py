from fastapi import Request, HTTPException 
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from ah.route_decorators import public_routes, public_route


SECRET_KEY = "your-secret-key"  # Change this to a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def middleware(request: Request, call_next):
    try:
        print('-------------------------- auth middleware ----------------------------')
        if request.url.path in public_routes:
            print('Public route: ', request.url.path)
            return await call_next(request)
        token = await security(request)
        print('token:', token)
        payload = decode_token(token.credentials)
        print('payload:', payload)
        request.state.user = payload
    except Exception as e:
        print('No valid token found')
        print("Not a public route: ", request.url.path)
        print('Redirecting to login')
        return RedirectResponse(url='/login')
    response = await call_next(request)
    return response

