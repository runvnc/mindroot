from fastapi import Request

try:
    from .language_detection import (
        _parse_accept_language_header,
        get_fallback_language,
        set_language_for_request
    )
except ImportError:
    # For standalone testing
    from language_detection import (
        _parse_accept_language_header,
        get_fallback_language,
        set_language_for_request
    )
import os

# Global variable to store the current request language
# This will be set by the middleware for each request
_current_request_language = None

def get_request_language() -> str:
    """
    Get the language that was detected for the current request.
    
    This function is called by the monkey patch system to get the
    language for template translation.
    
    Returns:
        Language code for the current request
    """
    global _current_request_language
    print(f"L8n: Current request language is '{_current_request_language}'")
    # If we have a request-specific language, use it
    if _current_request_language:
        return _current_request_language
    
    # Fallback to environment variable or default
    print("L8n: No request language set, falling back to environment variable or default")
    return os.environ.get('MINDROOT_LANGUAGE', 'en')

def detect_language_from_request(request: Request) -> str:
    """
    Detect the preferred language from a FastAPI request.
    
    Checks multiple sources in order of priority:
    1. URL parameter (?lang=es)
    2. Cookie value (mindroot_language)
    3. Accept-Language header
    4. Environment variable
    5. Default to 'en'
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Detected language code
    """
    # 1. Check URL parameter first (highest priority)
    print(f"L8n: Checking URL parameters for language: {request.query_params}")
    url_lang = request.query_params.get('lang')
    if url_lang:

        return get_fallback_language(url_lang.lower())
    
    # 2. Check cookie value
    print(f"L8n: Checking cookies for language: {request.cookies}")
    cookie_lang = request.cookies.get('mindroot_language')
    if cookie_lang:
        print(f"L8n: Found language in cookie: {cookie_lang}")
        return get_fallback_language(cookie_lang.lower())
    
    # 3. Check Accept-Language header
    print(f"L8n: Accept-Language header: {request.headers.get('accept-language')}")
    accept_language = request.headers.get('accept-language')
    if accept_language:
        print(f"L8n: Parsing Accept-Language header: {accept_language}")
        parsed_lang = _parse_accept_language_header(accept_language)
        if parsed_lang:
            print(f"L8n: Parsed language from header: {parsed_lang}")
            return get_fallback_language(parsed_lang)
    
    # 4. Check environment variable
    env_lang = os.environ.get('MINDROOT_LANGUAGE')
    if env_lang:
        return get_fallback_language(env_lang.lower())
    
    # 5. Default to English
    return 'en'

async def middleware(request: Request, call_next):
    """
    L8n middleware for language detection and setting.
    
    This middleware runs early in the request pipeline to:
    1. Detect the preferred language for the request
    2. Store it globally for use by the template system
    3. Set it in the request state for other components
    
    Args:
        request: FastAPI Request object
        call_next: Next middleware/handler in the chain
        
    Returns:
        Response from the next handler
    """
    global _current_request_language
    try:
        print("L8n middleware: Starting language detection")
        # Detect the language for this request
        detected_language = detect_language_from_request(request)

        print(f"L8n: Detected language '{detected_language}' for {request.url.path}")
        # Store it globally for the template system
        _current_request_language = detected_language
        
        # Also store it in request state for other components
        request.state.language = detected_language
        
        # Set it using the language detection system
        set_language_for_request(detected_language)
        
        # Debug logging (can be removed in production)
        print(f"L8n: Detected language '{detected_language}' for {request.url.path}")
        
        # Process the request
        response = await call_next(request)
        
        # Optionally set a cookie to remember the language preference
        # Only set if it was explicitly requested via URL parameter
        if request.query_params.get('lang'):
            response.set_cookie(
                key="mindroot_language",
                value=detected_language,
                max_age=30 * 24 * 60 * 60,  # 30 days
                httponly=True,
                samesite="lax"
            )
        
        return response
        
    except Exception as e:
        print(f"L8n middleware error: {e}")
        # If there's an error, continue with default language
        _current_request_language = 'en'
        request.state.language = 'en'
        return await call_next(request)
    
    finally:
        # Clean up the global variable after the request
        _current_request_language = None
