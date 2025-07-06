#!/usr/bin/env python3
"""
Debug script to test middleware import and functionality.
"""

import sys
from pathlib import Path

# Add the mindroot path
sys.path.insert(0, '/files/mindroot/src/mindroot')

try:
    print("Testing middleware import...")
    import coreplugins.l8n.middleware as mw
    print(f"✅ Middleware imported successfully")
    print(f"✅ Has middleware function: {hasattr(mw, 'middleware')}")
    print(f"✅ Middleware type: {type(mw.middleware)}")
    
    # Test if the function is callable
    import inspect
    print(f"✅ Function signature: {inspect.signature(mw.middleware)}")
    print(f"✅ Is coroutine function: {inspect.iscoroutinefunction(mw.middleware)}")
    
    # Test basic functionality
    print("\nTesting basic middleware functionality...")
    
    # Mock request and call_next
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/test'})
            self.query_params = {}
            self.cookies = {}
            self.headers = {}
            self.state = type('obj', (object,), {})
    
    class MockResponse:
        def __init__(self):
            self.cookies_set = {}
        def set_cookie(self, **kwargs):
            self.cookies_set.update(kwargs)
    
    async def mock_call_next(request):
        return MockResponse()
    
    # Test the middleware
    import asyncio
    
    async def test_middleware():
        request = MockRequest()
        try:
            response = await mw.middleware(request, mock_call_next)
            print(f"✅ Middleware executed successfully")
            print(f"✅ Request language set: {hasattr(request.state, 'language')}")
            if hasattr(request.state, 'language'):
                print(f"✅ Language: {request.state.language}")
            return True
        except Exception as e:
            print(f"❌ Middleware execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Run the test
    result = asyncio.run(test_middleware())
    
    if result:
        print("\n🎉 All middleware tests passed!")
    else:
        print("\n💥 Middleware tests failed!")
        
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
