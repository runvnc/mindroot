import os
import re
import json
from pathlib import Path
try:
    from lib.providers.commands import command, command_manager
except ImportError:
    from mindroot.lib.providers.commands import command, command_manager
from .utils import extract_plugin_root, get_localized_file_path, load_plugin_translations, get_plugin_translations_path
from mindroot.lib.utils.debug import debug_box
debug_box('l8n: Top of mod.py')
from .l8n_constants import *

def save_plugin_translations(plugin_path: str, translations: dict):
    """Save translations for a specific plugin to disk."""
    translations_file = get_plugin_translations_path(plugin_path)
    try:
        translations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(translations_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        return False
debug_box('l8n: defining command')
debug_box(f'l8n: command_manager has {len(command_manager.functions)} functions before registration')
debug_box(f'l8n: command_manager instance ID: {id(command_manager)}')

@command()
async def write_localized_file(original_path: str, content: str, context=None):
    """
    Write a localized version of a file with static placeholders.
    
    This command creates a localized version of a template or source file
    with __TRANSLATE_key__ placeholders that will be replaced with actual
    translations when the file is loaded.
    
    PLACEHOLDER FORMAT RULES:
    - Always use the exact format: __TRANSLATE_key_name__
    - Must start with __TRANSLATE_ and end with __
    - Use lowercase letters, numbers, and underscores only for the key name
    - Use descriptive, hierarchical key names like section_element or buttons_save
    - NO spaces, hyphens, or special characters in key names
    
    Args:
        original_path: Absolute path to the original file
        content: File content with __TRANSLATE_key__ placeholders
        context: Command context (optional)
    
    Examples:
        await write_localized_file(
            "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2",
            "<h1>__TRANSLATE_chat_title__</h1><button>__TRANSLATE_buttons_send__</button>"
        )
        
        await write_localized_file(
            "/some/path/src/my_plugin/templates/dashboard.jinja2",
            "<div>__TRANSLATE_dashboard_welcome__</div>"
        )
    """
    try:
        localized_path = get_localized_file_path(original_path)
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        with open(localized_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f'Localized file written to: {localized_path}'
    except Exception as e:
        return f'Error writing localized file: {str(e)}'

@command()
async def append_localized_file(original_path: str, content: str, context=None):
    """
    Append content to an existing localized file.
    
    Use this for large files that need to be built incrementally.
    Follow the same placeholder format rules as write_localized_file.
    
    Args:
        original_path: Absolute path to the original file
        content: Content to append with __TRANSLATE_key__ placeholders
        context: Command context (optional)
    
    Example:
        # First write the beginning
        await write_localized_file(
            "/path/to/large_template.jinja2",
            "<html><head><title>__TRANSLATE_page_title__</title></head>"
        )
        
        # Then append more sections
        await append_localized_file(
            "/path/to/large_template.jinja2",
            "<body><h1>__TRANSLATE_main_heading__</h1></body></html>"
        )
    """
    try:
        localized_path = get_localized_file_path(original_path)
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        with open(localized_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f'Content appended to: {localized_path}'
    except Exception as e:
        return f'Error appending to localized file: {str(e)}'

@command()
async def set_translations(original_path: str, language: str, translations: dict, context=None):
    """
    Set translations for a specific language and plugin.
    
    This command stores the translation mappings that will be used to replace
    __TRANSLATE_key__ placeholders in localized files. Translations are stored
    per plugin based on the provided file path.
    
    Args:
        original_path: Absolute path to a file in the plugin (used to identify the plugin)
        language: Language code (e.g., 'en', 'es', 'fr', 'de')
        translations: Dictionary mapping translation keys to translated text
        context: Command context (optional)
    
    Examples:
        await set_translations(
            "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2",
            'es', 
            {
                'chat_title': 'Interfaz de Chat',
                'buttons_send': 'Enviar Mensaje',
                'nav_home': 'Inicio',
                'error_connection_failed': 'Error de conexión'
            }
        )
        
        await set_translations(
            "/some/path/src/my_plugin/templates/dashboard.jinja2",
            'fr', 
            {
                'dashboard_welcome': 'Bienvenue au Tableau de Bord',
                'buttons_save': 'Enregistrer',
                'nav_home': 'Accueil'
            }
        )
    """
    try:
        if not isinstance(translations, dict):
            return 'Error: translations must be a dictionary'
        plugin_key = str(get_plugin_translations_path(original_path))
        plugin_translations = load_plugin_translations(original_path)
        invalid_keys = []
        for key in translations.keys():
            if not re.match('^[a-z0-9_]+$', key):
                invalid_keys.append(key)
        if invalid_keys:
            return f'Error: Invalid translation keys (use lowercase, numbers, underscores only): {invalid_keys}'
        if language not in plugin_translations:
            plugin_translations[language] = {}
        plugin_translations[language].update(translations)
        if save_plugin_translations(original_path, plugin_translations):
            TRANSLATIONS[plugin_key] = plugin_translations
            return f"Set {len(translations)} translations for language '{language}' in {Path(plugin_key).parent.name} plugin"
        else:
            return f'Error: Could not save translations'
    except Exception as e:
        return f'Error setting translations: {str(e)}'

@command()
async def get_translations(original_path: str=None, language: str=None, context=None):
    """
    Get translations for a specific plugin and language.
    
    Args:
        original_path: Absolute path to a file in the plugin (optional)
                      If not provided, returns all cached translations
        language: Language code to get translations for (optional)
        context: Command context (optional)
    
    Returns:
        Dictionary of translations
    
    Examples:
        # Get all translations for a plugin
        translations = await get_translations(
            "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2"
        )
        
        # Get Spanish translations for a plugin
        spanish = await get_translations(
            "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2",
            'es'
        )
        
        # Get all cached translations
        all_cached = await get_translations()
    """
    try:
        if original_path:
            plugin_translations = load_plugin_translations(original_path)
            plugin_key = str(get_plugin_translations_path(original_path))
            TRANSLATIONS[plugin_key] = plugin_translations
            if language:
                return plugin_translations.get(language, {})
            else:
                return plugin_translations
        else:
            return TRANSLATIONS
    except Exception as e:
        return f'Error getting translations: {str(e)}'

@command()
async def list_localized_files(context=None):
    """
    List all localized files that have been created.
    
    Returns:
        List of paths to localized files
    """
    try:
        localized_files = []
        if LOCALIZED_FILES_DIR.exists():
            for file_path in LOCALIZED_FILES_DIR.rglob('*.i18n.*'):
                localized_files.append(str(file_path.relative_to(LOCALIZED_FILES_DIR)))
        return {'count': len(localized_files), 'files': sorted(localized_files)}
    except Exception as e:
        return f'Error listing localized files: {str(e)}'
debug_box(f'l8n: command_manager has {len(command_manager.functions)} functions after registration')
debug_box('l8n: End of mod.py')