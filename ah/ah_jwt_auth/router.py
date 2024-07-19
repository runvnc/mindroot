from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .middleware import create_access_token, decode_token

router = APIRouter()
security = HTTPBearer()

@router.post("/login")
async def login(username: str, password: str):
    # Here you should verify the username and password
    # This is a simplified example
    if username == "testuser" and password == "testpass":
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

@router.get("/protected")
async def protected_route(token: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(token.credentials)
    return {"message": f"Hello, {payload['sub']}! This is a protected route."}
