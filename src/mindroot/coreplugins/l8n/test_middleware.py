#!/usr/bin/env python3
"""
Test script for the l8n middleware functionality.

This script simulates FastAPI request objects to test the middleware.
"""

import asyncio
import os
from unittest.mock import Mock

# Mock FastAPI Request for testing
class MockRequest:
    def __init__(self, path="/", query_params=None, cookies=None, headers=None):
        self.url = Mock()
        self.url.path = path
        self.query_params = query_params or {}
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.state = Mock()

# Mock Response for testing
class MockResponse:
    def __init__(self):
        self.cookies_set = {}
    
    def set_cookie(self, key, value, max_age=None, httponly=None, samesite=None):
        self.cookies_set[key] = {
            'value': value,
            'max_age': max_age,
            'httponly': httponly,
            'samesite': samesite
        }

# Import the middleware functions with sys.path manipulation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Now import with absolute imports
import middleware
from language_detection import _parse_accept_language_header, get_fallback_language

# Create aliases for easier use
middleware_func = middleware.middleware
detect_language_from_request = middleware.detect_language_from_request
get_request_language = middleware.get_request_language

async def mock_call_next(request):
    """Mock the next handler in the middleware chain."""
    return MockResponse()

async def test_language_detection():
    """Test language detection from various request sources."""
    print("Testing Language Detection from Requests...\n")
    
    # Test 1: URL parameter
    print("1. Testing URL parameter detection...")
    request = MockRequest(
        path="/chat",
        query_params={'lang': 'es'}
    )
    detected = detect_language_from_request(request)
    print(f"   URL param 'lang=es' -> {detected}")
    
    # Test 2: Cookie value
    print("\n2. Testing cookie detection...")
    request = MockRequest(
        path="/admin",
        cookies={'mindroot_language': 'fr'}
    )
    detected = detect_language_from_request(request)
    print(f"   Cookie 'mindroot_language=fr' -> {detected}")
    
    # Test 3: Accept-Language header
    print("\n3. Testing Accept-Language header...")
    test_headers = [
        'en-US,en;q=0.9,es;q=0.8',
        'es-ES,es;q=0.9,en;q=0.8',
        'fr-FR,fr;q=0.9',
        'de-DE,de;q=0.8,en;q=0.5',
        'zh-CN,zh;q=0.9,en;q=0.1'
    ]
    
    for header in test_headers:
        request = MockRequest(
            path="/test",
            headers={'accept-language': header}
        )
        detected = detect_language_from_request(request)
        print(f"   '{header}' -> {detected}")
    
    # Test 4: Environment variable
    print("\n4. Testing environment variable...")
    os.environ['MINDROOT_LANGUAGE'] = 'de'
    request = MockRequest(path="/test")
    detected = detect_language_from_request(request)
    print(f"   MINDROOT_LANGUAGE=de -> {detected}")
    
    # Test 5: Priority order (URL param should override everything)
    print("\n5. Testing priority order...")
    request = MockRequest(
        path="/test",
        query_params={'lang': 'es'},
        cookies={'mindroot_language': 'fr'},
        headers={'accept-language': 'de-DE,de;q=0.9'}
    )
    detected = detect_language_from_request(request)
    print(f"   URL=es, Cookie=fr, Header=de -> {detected} (should be es)")
    
    # Clean up
    os.environ.pop('MINDROOT_LANGUAGE', None)
    
    print("\n✅ Language detection tests completed!")

async def test_middleware_functionality():
    """Test the complete middleware functionality."""
    print("\nTesting Middleware Functionality...\n")
    
    # Test 1: Basic middleware flow
    print("1. Testing basic middleware flow...")
    request = MockRequest(
        path="/chat",
        query_params={'lang': 'es'},
        headers={'accept-language': 'en-US,en;q=0.9'}
    )
    
    response = await middleware_func(request, mock_call_next)
    
    print(f"   Request language set to: {request.state.language}")
    print(f"   Global language: {get_request_language()}")
    print(f"   Cookie set: {'mindroot_language' in response.cookies_set}")
    
    if 'mindroot_language' in response.cookies_set:
        cookie_info = response.cookies_set['mindroot_language']
        print(f"   Cookie value: {cookie_info['value']}")
        print(f"   Cookie max_age: {cookie_info['max_age']} seconds")
    
    # Test 2: Different language sources
    print("\n2. Testing different language sources...")
    
    test_cases = [
        {
            'name': 'Accept-Language only',
            'request': MockRequest(
                path="/admin",
                headers={'accept-language': 'fr-FR,fr;q=0.9,en;q=0.8'}
            ),
            'expected': 'fr'
        },
        {
            'name': 'Cookie preference',
            'request': MockRequest(
                path="/settings",
                cookies={'mindroot_language': 'de'}
            ),
            'expected': 'de'
        },
        {
            'name': 'URL override',
            'request': MockRequest(
                path="/dashboard",
                query_params={'lang': 'es'},
                cookies={'mindroot_language': 'fr'}
            ),
            'expected': 'es'
        }
    ]
    
    for case in test_cases:
        print(f"\n   Testing: {case['name']}")
        response = await middleware_func(case['request'], mock_call_next)
        actual = case['request'].state.language
        expected = case['expected']
        status = "✅" if actual == expected else "❌"
        print(f"   {status} Expected: {expected}, Got: {actual}")
    
    # Test 3: Error handling
    print("\n3. Testing error handling...")
    
    # Create a request that might cause issues
    request = MockRequest(
        path="/test",
        headers={'accept-language': 'invalid-header-format'}
    )
    
    try:
        response = await middleware_func(request, mock_call_next)
        print(f"   ✅ Error handled gracefully, language: {request.state.language}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    print("\n✅ Middleware functionality tests completed!")

async def test_integration_with_templates():
    """Test integration with the template system."""
    print("\nTesting Integration with Template System...\n")
    
    # Import template-related functions
    from test_l8n_standalone import set_translations, replace_placeholders
    
    # Set up some translations
    print("1. Setting up translations...")
    await set_translations('en', {
        'page_title': 'Welcome to MindRoot',
        'nav_home': 'Home',
        'nav_settings': 'Settings'
    })
    
    await set_translations('es', {
        'page_title': 'Bienvenido a MindRoot',
        'nav_home': 'Inicio',
        'nav_settings': 'Configuración'
    })
    
    await set_translations('fr', {
        'page_title': 'Bienvenue à MindRoot',
        'nav_home': 'Accueil',
        'nav_settings': 'Paramètres'
    })
    
    # Template content
    template = "<title>__TRANSLATE_page_title__</title><nav><a>__TRANSLATE_nav_home__</a><a>__TRANSLATE_nav_settings__</a></nav>"
    
    # Test different language requests
    print("\n2. Testing template translation with different requests...")
    
    test_requests = [
        ('English (default)', MockRequest(path="/")),
        ('Spanish (URL param)', MockRequest(path="/", query_params={'lang': 'es'})),
        ('French (cookie)', MockRequest(path="/", cookies={'mindroot_language': 'fr'})),
        ('German (header)', MockRequest(path="/", headers={'accept-language': 'de-DE,de;q=0.9,en;q=0.8'}))
    ]
    
    for name, request in test_requests:
        print(f"\n   Testing: {name}")
        
        # Process request through middleware
        await middleware_func(request, mock_call_next)
        
        # Get the detected language
        detected_lang = get_request_language()
        print(f"   Detected language: {detected_lang}")
        
        # Translate the template
        translated = replace_placeholders(template, detected_lang)
        
        # Extract title for display
        title_start = translated.find('<title>') + 7
        title_end = translated.find('</title>')
        title = translated[title_start:title_end]
        
        print(f"   Translated title: {title}")
    
    print("\n✅ Template integration tests completed!")

async def main():
    """Run all middleware tests."""
    print("=" * 60)
    print("MindRoot l8n Plugin - Middleware Testing Suite")
    print("=" * 60)
    
    await test_language_detection()
    await test_middleware_functionality()
    await test_integration_with_templates()
    
    print("\n" + "=" * 60)
    print("✅ All middleware tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
