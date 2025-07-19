#!/usr/bin/env python3
"""
Standalone test script for the l8n localization plugin.

This script tests the core functionality without MindRoot dependencies.
"""

import asyncio
import os
import re
from pathlib import Path

# Simulate the command decorator for testing
def command():
    def decorator(func):
        return func
    return decorator

# Copy the core functions from mod.py without MindRoot dependencies
TRANSLATIONS = {}
LOCALIZED_FILES_DIR = Path(__file__).parent / "localized_files"

def extract_plugin_root(absolute_path: str) -> str:
    """Extract the plugin root from an absolute path."""
    path = Path(absolute_path)
    parts = path.parts
    
    # Find coreplugins in the path
    if 'coreplugins' in parts:
        coreplugins_idx = parts.index('coreplugins')
        if coreplugins_idx + 1 < len(parts):
            return '/'.join(parts[coreplugins_idx + 1:])
    
    # Find src/[plugin_name] pattern for external plugins
    for i, part in enumerate(parts):
        if part == 'src' and i + 1 < len(parts):
            potential_plugin = parts[i + 1]
            if i + 2 < len(parts):  # Has more path after src/plugin_name
                return '/'.join(parts[i + 1:])
    
    # Fallback: return the filename
    return path.name

def get_localized_file_path(original_path: str) -> Path:
    """Convert an original file path to its localized version path."""
    plugin_root = extract_plugin_root(original_path)
    path = Path(plugin_root)
    
    # Determine if this is a core plugin or external plugin
    if any(core_plugin in plugin_root for core_plugin in ['chat', 'admin', 'l8n']):
        # Core plugin
        base_dir = LOCALIZED_FILES_DIR / "coreplugins"
    else:
        # External plugin
        base_dir = LOCALIZED_FILES_DIR / "external_plugins"
    
    # Add .i18n before the file extension
    stem = path.stem
    suffix = path.suffix
    new_filename = f"{stem}.i18n{suffix}"
    
    localized_path = base_dir / path.parent / new_filename
    return localized_path

async def write_localized_file(original_path: str, content: str, context=None):
    """Write a localized version of a file with static placeholders."""
    try:
        localized_path = get_localized_file_path(original_path)
        
        # Create directory if it doesn't exist
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        with open(localized_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Localized file written to: {localized_path}"
    
    except Exception as e:
        return f"Error writing localized file: {str(e)}"

async def append_localized_file(original_path: str, content: str, context=None):
    """Append content to an existing localized file."""
    try:
        localized_path = get_localized_file_path(original_path)
        
        # Create directory if it doesn't exist
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append the content
        with open(localized_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        return f"Content appended to: {localized_path}"
    
    except Exception as e:
        return f"Error appending to localized file: {str(e)}"

async def set_translations(language: str, translations: dict, context=None):
    """Set translations for a specific language."""
    try:
        if not isinstance(translations, dict):
            return "Error: translations must be a dictionary"
        
        # Validate translation keys
        invalid_keys = []
        for key in translations.keys():
            if not re.match(r'^[a-z0-9_]+$', key):
                invalid_keys.append(key)
        
        if invalid_keys:
            return f"Error: Invalid translation keys: {invalid_keys}"
        
        # Store translations
        if language not in TRANSLATIONS:
            TRANSLATIONS[language] = {}
        
        TRANSLATIONS[language].update(translations)
        
        return f"Set {len(translations)} translations for language '{language}'. Total languages: {len(TRANSLATIONS)}"
    
    except Exception as e:
        return f"Error setting translations: {str(e)}"

async def get_translations(language: str = None, context=None):
    """Get translations for a specific language or all languages."""
    try:
        if language:
            return TRANSLATIONS.get(language, {})
        else:
            return TRANSLATIONS
    
    except Exception as e:
        return f"Error getting translations: {str(e)}"

async def list_localized_files(context=None):
    """List all localized files that have been created."""
    try:
        localized_files = []
        
        if LOCALIZED_FILES_DIR.exists():
            for file_path in LOCALIZED_FILES_DIR.rglob("*.i18n.*"):
                localized_files.append(str(file_path.relative_to(LOCALIZED_FILES_DIR)))
        
        return {
            "count": len(localized_files),
            "files": sorted(localized_files)
        }
    
    except Exception as e:
        return f"Error listing localized files: {str(e)}"

def replace_placeholders(content: str, language: str) -> str:
    """Replace __TRANSLATE_key__ placeholders with actual translations."""
    if language not in TRANSLATIONS:
        return content
    
    translations = TRANSLATIONS[language]
    
    def replace_match(match):
        key = match.group(1)
        return translations.get(key, match.group(0))  # Return original if no translation
    
    # Replace all __TRANSLATE_key__ patterns
    return re.sub(r'__TRANSLATE_([a-z0-9_]+)__', replace_match, content)

async def test_basic_functionality():
    """Test the basic l8n functionality."""
    print("Testing MindRoot l8n Plugin (Standalone)...\n")
    
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
    
    # Test 9: Check created file content
    print("\n7. Checking created file content...")
    localized_path = get_localized_file_path(test_path)
    if localized_path.exists():
        with open(localized_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        print(f"   File content: {repr(file_content)}")
        
        # Test replacement on actual file content
        spanish_file_result = replace_placeholders(file_content, 'es')
        print(f"   Spanish version: {spanish_file_result}")
    else:
        print(f"   File not found: {localized_path}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
