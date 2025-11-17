"""
Standalone test script for the l8n localization plugin.

This script tests the core functionality without MindRoot dependencies.
"""
import asyncio
import os
import re
from pathlib import Path

def command():

    def decorator(func):
        return func
    return decorator
TRANSLATIONS = {}
LOCALIZED_FILES_DIR = Path(__file__).parent / 'localized_files'

def extract_plugin_root(absolute_path: str) -> str:
    """Extract the plugin root from an absolute path."""
    path = Path(absolute_path)
    parts = path.parts
    if 'coreplugins' in parts:
        coreplugins_idx = parts.index('coreplugins')
        if coreplugins_idx + 1 < len(parts):
            return '/'.join(parts[coreplugins_idx + 1:])
    for i, part in enumerate(parts):
        if part == 'src' and i + 1 < len(parts):
            potential_plugin = parts[i + 1]
            if i + 2 < len(parts):
                return '/'.join(parts[i + 1:])
    return path.name

def get_localized_file_path(original_path: str) -> Path:
    """Convert an original file path to its localized version path."""
    plugin_root = extract_plugin_root(original_path)
    path = Path(plugin_root)
    if any((core_plugin in plugin_root for core_plugin in ['chat', 'admin', 'l8n'])):
        base_dir = LOCALIZED_FILES_DIR / 'coreplugins'
    else:
        base_dir = LOCALIZED_FILES_DIR / 'external_plugins'
    stem = path.stem
    suffix = path.suffix
    new_filename = f'{stem}.i18n{suffix}'
    localized_path = base_dir / path.parent / new_filename
    return localized_path

async def write_localized_file(original_path: str, content: str, context=None):
    """Write a localized version of a file with static placeholders."""
    try:
        localized_path = get_localized_file_path(original_path)
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        with open(localized_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f'Localized file written to: {localized_path}'
    except Exception as e:
        return f'Error writing localized file: {str(e)}'

async def append_localized_file(original_path: str, content: str, context=None):
    """Append content to an existing localized file."""
    try:
        localized_path = get_localized_file_path(original_path)
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        with open(localized_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f'Content appended to: {localized_path}'
    except Exception as e:
        return f'Error appending to localized file: {str(e)}'

async def set_translations(language: str, translations: dict, context=None):
    """Set translations for a specific language."""
    try:
        if not isinstance(translations, dict):
            return 'Error: translations must be a dictionary'
        invalid_keys = []
        for key in translations.keys():
            if not re.match('^[a-z0-9_]+$', key):
                invalid_keys.append(key)
        if invalid_keys:
            return f'Error: Invalid translation keys: {invalid_keys}'
        if language not in TRANSLATIONS:
            TRANSLATIONS[language] = {}
        TRANSLATIONS[language].update(translations)
        return f"Set {len(translations)} translations for language '{language}'. Total languages: {len(TRANSLATIONS)}"
    except Exception as e:
        return f'Error setting translations: {str(e)}'

async def get_translations(language: str=None, context=None):
    """Get translations for a specific language or all languages."""
    try:
        if language:
            return TRANSLATIONS.get(language, {})
        else:
            return TRANSLATIONS
    except Exception as e:
        return f'Error getting translations: {str(e)}'

async def list_localized_files(context=None):
    """List all localized files that have been created."""
    try:
        localized_files = []
        if LOCALIZED_FILES_DIR.exists():
            for file_path in LOCALIZED_FILES_DIR.rglob('*.i18n.*'):
                localized_files.append(str(file_path.relative_to(LOCALIZED_FILES_DIR)))
        return {'count': len(localized_files), 'files': sorted(localized_files)}
    except Exception as e:
        return f'Error listing localized files: {str(e)}'

def replace_placeholders(content: str, language: str) -> str:
    """Replace __TRANSLATE_key__ placeholders with actual translations."""
    if language not in TRANSLATIONS:
        return content
    translations = TRANSLATIONS[language]

    def replace_match(match):
        key = match.group(1)
        return translations.get(key, match.group(0))
    return re.sub('__TRANSLATE_([a-z0-9_]+)__', replace_match, content)

async def test_basic_functionality():
    """Test the basic l8n functionality."""
    test_path = '/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2'
    test_content = '<h1>__TRANSLATE_chat_title__</h1><button>__TRANSLATE_buttons_send__</button>'
    result = await write_localized_file(test_path, test_content)
    append_content = '<p>__TRANSLATE_welcome_message__</p>'
    result = await append_localized_file(test_path, append_content)
    spanish_translations = {'chat_title': 'Interfaz de Chat', 'buttons_send': 'Enviar Mensaje', 'welcome_message': 'Bienvenido al chat'}
    result = await set_translations('es', spanish_translations)
    french_translations = {'chat_title': 'Interface de Chat', 'buttons_send': 'Envoyer le Message', 'welcome_message': 'Bienvenue dans le chat'}
    result = await set_translations('fr', french_translations)
    es_translations = await get_translations('es')
    all_translations = await get_translations()
    files_result = await list_localized_files()
    test_template = '<h1>__TRANSLATE_chat_title__</h1><button>__TRANSLATE_buttons_send__</button><p>__TRANSLATE_welcome_message__</p>'
    spanish_result = replace_placeholders(test_template, 'es')
    french_result = replace_placeholders(test_template, 'fr')
    unknown_result = replace_placeholders(test_template, 'de')
    localized_path = get_localized_file_path(test_path)
    if localized_path.exists():
        with open(localized_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        spanish_file_result = replace_placeholders(file_content, 'es')
if __name__ == '__main__':
    asyncio.run(test_basic_functionality())