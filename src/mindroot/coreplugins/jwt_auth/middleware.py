from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from lib.route_decorators import public_routes, public_route, public_static
from coreplugins.api_keys import api_key_manager
from lib.providers.services import service_manager
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

        # Check for API key in query parameters
        api_key = request.query_params.get('api_key')
        if api_key:
            print('Found API key in query parameters')
            key_data = api_key_manager.validate_key(api_key)
            if key_data:
                print("Validated API Key, key_data is", key_data)
                username = key_data['username']
                print("Trying to get user data")
                user_data = await service_manager.get_user_data(username)

                if user_data:
                    request.state.user = user_data
                    
                    # Create JWT token for persistent session
                    token = create_access_token({"sub": username})
                    
                    # Get response and set cookie
                    response = await call_next(request)
                    response.set_cookie(
                        key="access_token",
                        value=token,
                        httponly=True,
                        partitioned=True,
                        samesite='None',  # Adjust to 'None' if needed for cross-origin
                        secure=True  # Assuming HTTPS is used
                    )
                    return response
                else:
                    print(f"User {username} for key {api_key} not found")
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"User '{username}' for API key {api_key} not found"}
                    )
            else:
                print("Could not validate API key, key_data returned as", key_data)
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid API key"}
                )

        if request.url.path in public_routes:
            print('Public route: ', request.url.path)
            return await call_next(request)
        elif any([request.url.path.startswith(path) for path in public_static]):
            return await call_next(request)
        else:
            print('Not a public route: ', request.url.path)

        # Check for token in cookies first
        token = request.cookies.get("access_token")
        if token:
            payload = decode_token(token)
            if payload:
                # Get username from token
                username = payload['sub']
                
                user_data = await service_manager.get_user_data(username)
                request.state.user = user_data 
                if user_data:
                    return await call_next(request)
                else:
                    print("User data not found, redirecting to login..")
                    return RedirectResponse(url="/login")
            else:
                print("Invalid or expired token, redirecting to login..")
                return RedirectResponse(url="/login")

        print("..Did not find token in cookies..")
        try:
            # Try bearer token
            token = await security(request)
        except HTTPException as e:
            print('HTTPException: No valid token found: ', e)
            return RedirectResponse(url="/login")

        if token:
            payload = decode_token(token.credentials)
            if payload:
                username = payload['sub']
                user_data = await service_manager.get_user_data(username)
                
                if user_data:
                    request.state.user = {
                        "username": username,
                        "token_data": payload,
                        **user_data
                    }
                    return await call_next(request)
                else:
                    print("User data not found, redirecting to login..")
                    return RedirectResponse(url="/login")
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
