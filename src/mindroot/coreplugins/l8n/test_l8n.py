#!/usr/bin/env python3
"""
Simple test script for the l8n localization plugin.

This script tests the basic functionality of the localization commands
without requiring the full MindRoot environment.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mod import (
    write_localized_file,
    append_localized_file,
    set_translations,
    get_translations,
    list_localized_files,
    replace_placeholders
)

async def test_basic_functionality():
    """Test the basic l8n functionality."""
    print("Testing MindRoot l8n Plugin...\n")
    
    # Test 1: Create a localized file
    print("1. Testing write_localized_file...")
    test_path = "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2"
    test_content = "<h1>__TRANSLATE_chat_title__</h1><button>__TRANSLATE_buttons_send__</button>"
    
    result = await write_localized_file(test_path, test_content)
    print(f"   Result: {result}")
    
    # Test 2: Append to the file
    print("\n2. Testing append_localized_file...")
    append_content = "<p>__TRANSLATE_welcome_message__</p>"
    
    result = await append_localized_file(test_path, append_content)
    print(f"   Result: {result}")
    
    # Test 3: Set translations
    print("\n3. Testing set_translations...")
    spanish_translations = {
        'chat_title': 'Interfaz de Chat',
        'buttons_send': 'Enviar Mensaje',
        'welcome_message': 'Bienvenido al chat'
    }
    
    result = await set_translations('es', spanish_translations)
    print(f"   Result: {result}")
    
    # Test 4: Set more translations
    french_translations = {
        'chat_title': 'Interface de Chat',
        'buttons_send': 'Envoyer le Message',
        'welcome_message': 'Bienvenue dans le chat'
    }
    
    result = await set_translations('fr', french_translations)
    print(f"   Result: {result}")
    
    # Test 5: Get translations
    print("\n4. Testing get_translations...")
    es_translations = await get_translations('es')
    print(f"   Spanish translations: {es_translations}")
    
    all_translations = await get_translations()
    print(f"   All languages: {list(all_translations.keys())}")
    
    # Test 6: List localized files
    print("\n5. Testing list_localized_files...")
    files_result = await list_localized_files()
    print(f"   Result: {files_result}")
    
    # Test 7: Test placeholder replacement
    print("\n6. Testing placeholder replacement...")
    test_template = "<h1>__TRANSLATE_chat_title__</h1><button>__TRANSLATE_buttons_send__</button><p>__TRANSLATE_welcome_message__</p>"
    
    spanish_result = replace_placeholders(test_template, 'es')
    print(f"   Spanish: {spanish_result}")
    
    french_result = replace_placeholders(test_template, 'fr')
    print(f"   French: {french_result}")
    
    # Test 8: Test with unknown language (should return original)
    unknown_result = replace_placeholders(test_template, 'de')
    print(f"   German (unknown): {unknown_result}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
