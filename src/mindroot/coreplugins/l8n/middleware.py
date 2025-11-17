from fastapi import Request
try:
    from .language_detection import _parse_accept_language_header, get_fallback_language, set_language_for_request
except ImportError:
    from language_detection import _parse_accept_language_header, get_fallback_language, set_language_for_request
import os
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
    if _current_request_language:
        return _current_request_language
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
    url_lang = request.query_params.get('lang')
    if url_lang:
        return get_fallback_language(url_lang.lower())
    cookie_lang = request.cookies.get('mindroot_language')
    if cookie_lang:
        return get_fallback_language(cookie_lang.lower())
    accept_language = request.headers.get('accept-language')
    if accept_language:
        parsed_lang = _parse_accept_language_header(accept_language)
        if parsed_lang:
            return get_fallback_language(parsed_lang)
    env_lang = os.environ.get('MINDROOT_LANGUAGE')
    if env_lang:
        return get_fallback_language(env_lang.lower())
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
        detected_language = detect_language_from_request(request)
        _current_request_language = detected_language
        request.state.language = detected_language
        set_language_for_request(detected_language)
        response = await call_next(request)
        if request.query_params.get('lang'):
            response.set_cookie(key='mindroot_language', value=detected_language, max_age=30 * 24 * 60 * 60, httponly=True, samesite='lax')
        return response
    except Exception as e:
        _current_request_language = 'en'
        request.state.language = 'en'
        return await call_next(request)
    finally:
        _current_request_language = None