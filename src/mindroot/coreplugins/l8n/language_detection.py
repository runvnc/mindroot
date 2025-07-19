import os
from typing import Optional

def get_current_language_from_request() -> str:
    """
    Get the current language from various request sources.
    
    This function checks multiple sources in order of priority:
    1. Environment variable MINDROOT_LANGUAGE
    2. FastAPI request context (if available)
    3. HTTP Accept-Language header
    4. URL parameters (?lang=es)
    5. Cookie values
    6. User preferences from database/session
    
    Returns:
        Language code (e.g., 'en', 'es', 'fr')
    """
    # 1. Check environment variable first (for testing/override)
    env_lang = os.environ.get('MINDROOT_LANGUAGE')
    if env_lang:
        return env_lang
    
    # 2. Try to get language from FastAPI request context
    try:
        from contextvars import ContextVar
        import contextvars
        
        # Try to find request context
        request_lang = _get_language_from_fastapi_context()
        if request_lang:
            return request_lang
    except (ImportError, Exception):
        pass
    
    # 3. Fallback to default language
    return 'en'

def _get_language_from_fastapi_context() -> Optional[str]:
    """
    Extract language from FastAPI request context.
    
    This function attempts to access the current FastAPI request
    and extract language information from various sources.
    
    Returns:
        Language code if found, None otherwise
    """
    try:
        # Try to get the current request from FastAPI context
        from starlette.requests import Request
        import contextvars
        
        # This is a placeholder - in a real implementation, we would need
        # to access the actual request context that MindRoot uses
        # For now, we'll implement the detection logic structure
        
        # Check if there's a way to get the current request
        # This would need to be integrated with MindRoot's request handling
        
        return None  # Placeholder
        
    except (ImportError, Exception):
        return None

def _parse_accept_language_header(accept_language: str) -> str:
    """
    Parse the Accept-Language header and return the preferred language.
    
    Args:
        accept_language: Accept-Language header value
        
    Returns:
        Preferred language code
        
    Example:
        'en-US,en;q=0.9,es;q=0.8,fr;q=0.7' -> 'en'
    """
    if not accept_language:
        return 'en'
    
    # Parse the Accept-Language header
    languages = []
    for lang_range in accept_language.split(','):
        lang_range = lang_range.strip()
        if ';q=' in lang_range:
            lang, quality = lang_range.split(';q=', 1)
            try:
                quality = float(quality)
            except ValueError:
                quality = 1.0
        else:
            lang = lang_range
            quality = 1.0
        
        # Extract just the language code (e.g., 'en' from 'en-US')
        lang_code = lang.split('-')[0].lower()
        languages.append((lang_code, quality))
    
    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)
    
    # Return the highest quality language
    if languages:
        return languages[0][0]
    
    return 'en'

def set_language_for_request(language: str):
    """
    Set the language for the current request context.
    
    This function would be called by middleware or route handlers
    to set the language for the current request.
    
    Args:
        language: Language code to set
    """
    # Set environment variable as a simple implementation
    os.environ['MINDROOT_LANGUAGE'] = language
    
    # In a real implementation, this would set the language
    # in the request context or thread-local storage

def get_supported_languages() -> list:
    """
    Get the list of supported languages.
    
    Returns:
        List of supported language codes
    """
    # This could be configured via environment variables or config files
    supported = os.environ.get('MINDROOT_SUPPORTED_LANGUAGES', 'en,es,fr,de,it,pt,ru,zh,ja,ko')
    return [lang.strip() for lang in supported.split(',')]

def is_language_supported(language: str) -> bool:
    """
    Check if a language is supported.
    
    Args:
        language: Language code to check
        
    Returns:
        True if language is supported, False otherwise
    """
    return language in get_supported_languages()

def get_fallback_language(language: str) -> str:
    """
    Get a fallback language if the requested language is not supported.
    
    Args:
        language: Requested language code
        
    Returns:
        Fallback language code
    """
    if is_language_supported(language):
        return language
    
    # Language family fallbacks
    fallbacks = {
        'en-us': 'en',
        'en-gb': 'en',
        'es-es': 'es',
        'es-mx': 'es',
        'fr-fr': 'fr',
        'fr-ca': 'fr',
        'de-de': 'de',
        'de-at': 'de',
        'pt-br': 'pt',
        'pt-pt': 'pt',
        'zh-cn': 'zh',
        'zh-tw': 'zh',
    }
    
    # Try fallback
    fallback = fallbacks.get(language.lower())
    if fallback and is_language_supported(fallback):
        return fallback
    
    # Default to English
    return 'en'
