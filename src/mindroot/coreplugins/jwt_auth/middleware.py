from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from lib.route_decorators import public_routes, public_route, public_static
from coreplugins.api_keys import api_key_manager
from lib.providers.services import service_manager
import os
from lib.session_files import load_session_data
from lib.utils.debug import debug_box
import secrets
from pathlib import Path

def get_or_create_jwt_secret():
    secret_key = os.environ.get("JWT_SECRET_KEY", None)
    
    if secret_key:
        print("JWT_SECRET_KEY found in environment variables")
        return secret_key
    
    # Check if .env file exists and contains JWT_SECRET_KEY
    env_path = Path.cwd() / ".env"
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith('JWT_SECRET_KEY='):
                    # Extract the key value
                    key_value = line.strip().split('=', 1)[1]
                    if key_value:
                        print(f"JWT_SECRET_KEY found in {env_path}")
                        # Also set it in environment for current session
                        os.environ['JWT_SECRET_KEY'] = key_value
                        return key_value
    
    # If we get here, no key was found anywhere, so generate one
    print("JWT_SECRET_KEY not found, generating new key...")
    secret_key = secrets.token_urlsafe(32)
    
    # Save to .env file
    # Check if file exists and needs a newline before appending
    needs_newline = False
    if env_path.exists() and env_path.stat().st_size > 0:
        with open(env_path, 'rb') as f:
            f.seek(-1, 2)  # Go to last byte
            last_char = f.read(1)
            needs_newline = last_char != b'\n'
    
    with open(env_path, 'a') as f:
        if needs_newline:
            f.write('\n')
        f.write(f"JWT_SECRET_KEY={secret_key}\n")
    
    print(f"Generated new JWT_SECRET_KEY and saved to {env_path}")
    os.environ['JWT_SECRET_KEY'] = secret_key
        
    return secret_key

# Get or create the secret key
SECRET_KEY = get_or_create_jwt_secret()
print(f"JWT_SECRET_KEY loaded successfully")

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
        if request.url.path.endswith('events'):
            debug_box("events:" + request.url.path)

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
                    request.state.access_token = token
                    # Get response and set cookie
                    response = await call_next(request)
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
        if request.url.path.startswith("/imgs/"):
            return await call_next(request)
        try:
            path_parts = request.url.path.split('/')
            # filter empty "" strings
            path_parts = list(filter(None, path_parts))
            print(f"Request path split is {path_parts}")
            plugin_name = path_parts[0]
            static_part = path_parts[1]
            filename = path_parts[-1]
            print(f"Checking for static file: {plugin_name} {static_part} {filename}")
            if static_part == 'static':
                if filename.endswith('.js') or filename.endswith('.css') or filename.endswith('.png') or filename.endswith('.mp4'):
                    print('Static file requested:', filename)
                    return await call_next(request)
        except Exception as e:
            print("Error checking for static file", e)
            pass
        print("Did not find static file")
        if request.url.path in public_routes:
            print('Public route: ', request.url.path)
            return await call_next(request)
        elif any([request.url.path.startswith(path) for path in public_static]):
            return await call_next(request)
        else:
            print('Not a public route: ', request.url.path)

        # Check for token in cookies first
        token = request.cookies.get("access_token")
        #token = None
        if token:
            print("Trying to decode token..")
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
        else:
            print("..Did not find token in cookies..")
        try:
            print("Trying bearer token..")
            token = await security(request)
        except HTTPException as e:
            print('Bearer header: No valid token found: ', e)
            print("Trying session context..")
            try:
                session_id = request.url.path.split('/')[-1]
                token = await load_session_data(session_id, "access_token")
                if token:
                    print("Retrieved token from session file")
                    print(token)
                else:
                    print("No token found in session file")
            except Exception as e:
                print("Error loading session data")
                print(e)

        if token:
            if hasattr(token, 'credentials'):
                payload = decode_token(token.credentials)
            else:
                payload = decode_token(token)
            if payload:
                username = payload['sub']
                user_data = await service_manager.get_user_data(username)
                
                if user_data:
                    request.state.user = user_data
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
