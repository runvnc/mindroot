from fastapi import APIRouter, Depends, HTTPException, Form, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .middleware import create_access_token, decode_token
from lib.route_decorators import public_routes, public_route
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

#@router.post("/login")
#@public_route()
#async def login(response: Response, username: str = Form(...), password: str = Form(...)):
#    print("login()")
#    if username == "testuser" and password == "testpass":
#        access_token = create_access_token(data={"sub": username})
#        response.set_cookie(key="access_token", value=access_token, max_age=604800)
#        return {"access_token": access_token, "token_type": "bearer"}
#    raise HTTPException(status_code=400, detail="Incorrect username or password")

@router.get("/protected")
async def protected_route(token: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(token.credentials)
    return {"message": f"Hello, {payload['sub']}! This is a protected route."}
