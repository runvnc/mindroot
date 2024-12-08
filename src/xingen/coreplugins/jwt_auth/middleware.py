from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from lib.route_decorators import public_routes, public_route
import os

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", None)

if SECRET_KEY is None:
    raise ValueError("JWT_SECRET_KEY environment variable not set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 1 week

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
        print("Token has expired")
        return False
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False

async def middleware(request: Request, call_next):
    try:
        print('-------------------------- auth middleware ----------------------------')
        print('Request URL:', request.url.path)
        if request.url.path in public_routes:
            print('Public route: ', request.url.path)
            return await call_next(request)
        else:
            print('Not a public route: ', request.url.path)
            # public_routes is set, iterate and print all
            #print("Printing all public routes: ")
            #for route in public_routes:
            #    print('Public route: ', route)

        token = request.cookies.get("access_token")
        if token:
            payload = decode_token(token)
            if payload:
                request.state.user = payload
                return await call_next(request)
            else:
                print("Invalid or expired token, redirecting to login..")
                return RedirectResponse(url="/login")
                #return JSONResponse(
                #    status_code=401,
                #    content={"detail": "Invalid or expired token"}
                #)

        print("..Did not find token in cookies..")
        try:
            token = await security(request)
        except HTTPException as e:
            print('HTTPException: No valid token found: ', e)
            return RedirectResponse(url="/login")

        if token:
            payload = decode_token(token.credentials)
            if payload:
                request.state.user = payload
                return await call_next(request)
            else:
                print("Invalid or expired token, redirecting to login..")
                return RedirectResponse(url="/login")

        print('No valid token found')
        return RedirectResponse(url="/login")

    except HTTPException as e:
        print('HTTPException:', e)
        return RedirectResponse(url="/login")

    except Exception as e:
        print('Error:', e)
        if 'does not exist' in str(e).lower() or 'not found' in str(e).lower():
            return JSONResponse(
                status_code=404,
                content={"detail": f"Resource not found: {str(e)}"}
            )

        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

    response = await call_next(request)
    return response
