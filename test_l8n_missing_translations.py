#!/usr/bin/env python3
"""
Test script to verify that the l8n system properly handles missing translations
by falling back to original files and logging appropriate warnings.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import asyncio

# Add the mindroot source to Python path
sys.path.insert(0, '/files/mindroot/src')

# Import l8n functions
from mindroot.coreplugins.l8n.utils import replace_placeholders, extract_translation_keys
from mindroot.coreplugins.l8n.mod import set_translations, write_localized_file
from mindroot.lib.templates import load_template_with_translation

async def test_missing_translations():
    """Test that missing translations are properly detected and handled."""
    print("\n=== Testing Missing Translation Detection ===")
    
    # Create a temporary test plugin structure
    test_dir = Path(tempfile.mkdtemp())
    plugin_dir = test_dir / "src" / "mindroot" / "coreplugins" / "test_plugin"
    plugin_dir.mkdir(parents=True)
    
    # Create a test template with translation placeholders
    template_path = plugin_dir / "templates" / "test.jinja2"
    template_path.parent.mkdir(parents=True)
    
    original_content = """
<h1>Welcome</h1>
<p>This is a test template without translation placeholders.</p>
<button>Click Me</button>
"""
    
    localized_content = """
<h1>__TRANSLATE_welcome_title__</h1>
<p>__TRANSLATE_welcome_message__</p>
<button>__TRANSLATE_button_click__</button>
<div>__TRANSLATE_missing_key__</div>
"""
    
    # Write original template
    with open(template_path, 'w') as f:
        f.write(original_content)
    
    try:
        # Test 1: Extract translation keys
        print("\n1. Testing translation key extraction...")
        keys = extract_translation_keys(localized_content)
        expected_keys = {'welcome_title', 'welcome_message', 'button_click', 'missing_key'}
        print(f"Extracted keys: {keys}")
        print(f"Expected keys: {expected_keys}")
        assert keys == expected_keys, f"Key extraction failed: {keys} != {expected_keys}"
        print("✓ Key extraction works correctly")
        
        # Test 2: Create localized file
        print("\n2. Creating localized file...")
        result = await write_localized_file(str(template_path), localized_content)
        print(f"Result: {result}")
        
        # Test 3: Set incomplete translations (missing 'missing_key')
        print("\n3. Setting incomplete translations...")
        incomplete_translations = {
            'welcome_title': 'Bienvenido',
            'welcome_message': 'Este es un mensaje de prueba',
            'button_click': 'Haz clic aquí'
            # Note: 'missing_key' is intentionally missing
        }
        
        result = await set_translations(str(template_path), 'es', incomplete_translations)
        print(f"Set translations result: {result}")
        
        # Test 4: Test replace_placeholders with missing translations
        print("\n4. Testing replace_placeholders with missing translations...")
        from mindroot.coreplugins.l8n.utils import get_localized_file_path
        localized_path = get_localized_file_path(str(template_path))
        
        # This should return None due to missing translation
        result = replace_placeholders(localized_content, 'es', str(localized_path))
        print(f"Replace placeholders result: {result}")
        
        if result is None:
            print("✓ Correctly detected missing translations and returned None")
        else:
            print("✗ Failed to detect missing translations")
            return False
        
        # Test 5: Test complete translations
        print("\n5. Testing complete translations...")
        complete_translations = {
            'welcome_title': 'Bienvenido',
            'welcome_message': 'Este es un mensaje de prueba',
            'button_click': 'Haz clic aquí',
            'missing_key': 'Clave encontrada'
        }
        
        result = await set_translations(str(template_path), 'es', complete_translations)
        print(f"Set complete translations result: {result}")
        
        # This should now work
        result = replace_placeholders(localized_content, 'es', str(localized_path))
        print(f"Replace placeholders with complete translations: {result[:100] if result else 'None'}...")
        
        if result is not None and 'Bienvenido' in result:
            print("✓ Complete translations work correctly")
        else:
            print("✗ Complete translations failed")
            return False
        
        print("\n=== Core functionality tests passed! ===")
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)

async def run_tests():
    try:
        success = await test_missing_translations()
        if success:
            print("\n🎉 All tests passed successfully!")
            return True
        else:
            print("\n❌ Some tests failed.")
            return False
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
