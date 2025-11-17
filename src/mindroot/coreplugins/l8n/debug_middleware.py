"""
Debug script to test middleware import and functionality.
"""
import sys
from pathlib import Path
sys.path.insert(0, '/files/mindroot/src/mindroot')
try:
    import coreplugins.l8n.middleware as mw
    import inspect

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
    import asyncio

    async def test_middleware():
        request = MockRequest()
        try:
            response = await mw.middleware(request, mock_call_next)
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    result = asyncio.run(test_middleware())
except Exception as e:
    import traceback
    traceback.print_exc()