#!/usr/bin/env python3
"""Test script for the Protocol-based typed service access.

This script verifies that the Protocol system works correctly.
Run from the mindroot directory:
    python test_protocols.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'mindroot'))

def test_protocol_imports():
    """Test that protocol modules can be imported."""
    print("Testing protocol imports...")
    
    try:
        from lib.providers.protocols.common import LLM, Image, TTS, STT, WebSearch
        from lib.providers.protocols.registry import (
            register_protocol, get_protocol, list_protocols,
            ServiceProxy, map_method_to_service, LazyTypedProxy,
            create_lazy_proxy
        )
        print("  OK - All protocol imports successful")
        return True
    except ImportError as e:
        print(f"  FAIL - Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_protocol_registry():
    """Test protocol registration and lookup."""
    print("Testing protocol registry...")
    
    from lib.providers.protocols.registry import (
        register_protocol, get_protocol, list_protocols
    )
    from lib.providers.protocols.common import LLM
    
    # Check that common protocols are registered
    protocols = list_protocols()
    print(f"  Registered protocols: {list(protocols.keys())}")
    
    # Verify LLM is registered
    llm_proto = get_protocol('llm')
    if llm_proto is LLM:
        print("  OK - LLM protocol registered correctly")
    else:
        print("  FAIL - LLM protocol not found")
        return False
    
    # Test custom protocol registration
    from typing import Protocol, runtime_checkable
    
    @runtime_checkable
    class TestProtocol(Protocol):
        async def test_method(self, x: int) -> str: ...
    
    register_protocol('test', TestProtocol)
    
    retrieved = get_protocol('test')
    if retrieved is TestProtocol:
        print("  OK - Custom protocol registration works")
    else:
        print("  FAIL - Custom protocol registration failed")
        return False
    
    return True

def test_service_proxy():
    """Test ServiceProxy creation and method delegation."""
    print("Testing ServiceProxy...")
    
    from lib.providers.protocols.registry import ServiceProxy
    from lib.providers.protocols.common import LLM
    
    # Create a mock manager
    class MockManager:
        async def execute(self, name, *args, **kwargs):
            return f"Called {name} with args={args}, kwargs={kwargs}"
    
    manager = MockManager()
    proxy = ServiceProxy(manager, LLM)
    
    # Check that proxy has the expected methods via __getattr__
    method = proxy.stream_chat
    if callable(method):
        print("  OK - ServiceProxy creates callable methods")
    else:
        print("  FAIL - ServiceProxy method creation failed")
        return False
    
    return True

def test_lazy_typed_proxy():
    """Test LazyTypedProxy initialization."""
    print("Testing LazyTypedProxy...")
    
    from lib.providers.protocols.registry import LazyTypedProxy
    from lib.providers.protocols.common import LLM
    
    # Create a lazy proxy
    lazy = LazyTypedProxy(LLM)
    
    # Check repr before initialization
    repr_str = repr(lazy)
    if 'lazy' in repr_str and 'LLM' in repr_str:
        print("  OK - LazyTypedProxy repr shows lazy state")
    else:
        print(f"  FAIL - Unexpected repr: {repr_str}")
        return False
    
    return True

def test_pre_instantiated_proxies():
    """Test that pre-instantiated proxies are available."""
    print("Testing pre-instantiated proxies...")
    
    from lib.providers.protocols import llm, image, tts, stt, web_search
    from lib.providers.protocols.registry import LazyTypedProxy
    
    # Check that they are LazyTypedProxy instances
    proxies = [('llm', llm), ('image', image), ('tts', tts), ('stt', stt), ('web_search', web_search)]
    
    for name, proxy in proxies:
        if isinstance(proxy, LazyTypedProxy):
            print(f"  OK - {name} is a LazyTypedProxy")
        else:
            print(f"  FAIL - {name} is not a LazyTypedProxy: {type(proxy)}")
            return False
    
    return True

def test_protocol_structural_typing():
    """Test that Protocols work with structural typing."""
    print("Testing structural typing...")
    
    from lib.providers.protocols.common import LLM
    
    # Create a class that implements LLM structurally
    class FakeLLM:
        async def stream_chat(self, model, messages=None, context=None, 
                              num_ctx=200000, temperature=0.0, 
                              max_tokens=5000, num_gpu_layers=0):
            yield "test"
        
        async def chat(self, model, messages, context=None,
                       temperature=0.0, max_tokens=5000):
            return "test"
        
        async def format_image_message(self, pil_image, context=None):
            return {}
        
        async def get_service_models(self, context=None):
            return {}
    
    fake = FakeLLM()
    
    # With @runtime_checkable, isinstance should work
    if isinstance(fake, LLM):
        print("  OK - Structural typing works with @runtime_checkable")
    else:
        print("  FAIL - Structural typing check failed")
        return False
    
    return True

async def test_service_proxy_async():
    """Test ServiceProxy async method execution."""
    print("Testing ServiceProxy async execution...")
    
    from lib.providers.protocols.registry import ServiceProxy
    from lib.providers.protocols.common import LLM
    
    # Create a mock manager
    class MockManager:
        async def execute(self, name, *args, **kwargs):
            return f"Called {name}"
    
    manager = MockManager()
    proxy = ServiceProxy(manager, LLM)
    
    # Call the method
    result = await proxy.stream_chat('gpt-4', messages=[])
    
    if result == "Called stream_chat":
        print("  OK - ServiceProxy async execution works")
        return True
    else:
        print(f"  FAIL - Unexpected result: {result}")
        return False

def test_create_lazy_proxy():
    """Test the create_lazy_proxy helper function."""
    print("Testing create_lazy_proxy helper...")
    
    from lib.providers.protocols.registry import create_lazy_proxy, LazyTypedProxy
    from lib.providers.protocols.common import TTS
    
    proxy = create_lazy_proxy(TTS)
    
    if isinstance(proxy, LazyTypedProxy):
        print("  OK - create_lazy_proxy returns LazyTypedProxy")
        return True
    else:
        print(f"  FAIL - Unexpected type: {type(proxy)}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("MindRoot Protocol System Tests")
    print("="*60)
    print()
    
    tests = [
        test_protocol_imports,
        test_protocol_registry,
        test_service_proxy,
        test_lazy_typed_proxy,
        test_pre_instantiated_proxies,
        test_protocol_structural_typing,
        test_create_lazy_proxy,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  FAIL - Test raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()
    
    # Run async test
    import asyncio
    try:
        result = asyncio.run(test_service_proxy_async())
        results.append(result)
    except Exception as e:
        print(f"  FAIL - Async test raised exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    print()
    
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
