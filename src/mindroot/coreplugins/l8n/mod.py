import os
import re
from pathlib import Path
from lib.providers.commands import command

# Global storage for translations
# Structure: {language: {key: translation}}
TRANSLATIONS = {}

# Base directory for localized files
LOCALIZED_FILES_DIR = Path(__file__).parent / "localized_files"

def extract_plugin_root(absolute_path: str) -> str:
    """
    Extract the plugin root from an absolute path.
    
    For core plugins: everything after 'coreplugins/'
    For external plugins: everything after 'src/[plugin_name]/'
    
    Examples:
    - /files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2 -> chat/templates/chat.jinja2
    - /some/path/src/my_plugin/templates/page.jinja2 -> my_plugin/templates/page.jinja2
    """
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
            # Check if this looks like a plugin (has templates, static, etc.)
            potential_plugin = parts[i + 1]
            if i + 2 < len(parts):  # Has more path after src/plugin_name
                return '/'.join(parts[i + 1:])
    
    # Fallback: return the filename
    return path.name

def get_localized_file_path(original_path: str) -> Path:
    """
    Convert an original file path to its localized version path.
    
    Examples:
    - chat/templates/chat.jinja2 -> localized_files/coreplugins/chat/templates/chat.i18n.jinja2
    - my_plugin/templates/page.jinja2 -> localized_files/external_plugins/my_plugin/templates/page.i18n.jinja2
    """
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
        
        # Create directory if it doesn't exist
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        with open(localized_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Localized file written to: {localized_path}"
    
    except Exception as e:
        return f"Error writing localized file: {str(e)}"

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
        
        # Create directory if it doesn't exist
        localized_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append the content
        with open(localized_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        return f"Content appended to: {localized_path}"
    
    except Exception as e:
        return f"Error appending to localized file: {str(e)}"

@command()
async def set_translations(language: str, translations: dict, context=None):
    """
    Set translations for a specific language.
    
    This command stores the translation mappings that will be used to replace
    __TRANSLATE_key__ placeholders in localized files.
    
    Args:
        language: Language code (e.g., 'en', 'es', 'fr', 'de')
        translations: Dictionary mapping translation keys to translated text
        context: Command context (optional)
    
    Example:
        await set_translations('es', {
            'chat_title': 'Interfaz de Chat',
            'buttons_send': 'Enviar Mensaje',
            'nav_home': 'Inicio',
            'error_connection_failed': 'Error de conexión'
        })
        
        await set_translations('fr', {
            'chat_title': 'Interface de Chat',
            'buttons_send': 'Envoyer le Message',
            'nav_home': 'Accueil'
        })
    """
    try:
        if not isinstance(translations, dict):
            return "Error: translations must be a dictionary"
        
        # Validate translation keys (should match placeholder format)
        invalid_keys = []
        for key in translations.keys():
            if not re.match(r'^[a-z0-9_]+$', key):
                invalid_keys.append(key)
        
        if invalid_keys:
            return f"Error: Invalid translation keys (use lowercase, numbers, underscores only): {invalid_keys}"
        
        # Store translations
        if language not in TRANSLATIONS:
            TRANSLATIONS[language] = {}
        
        TRANSLATIONS[language].update(translations)
        
        return f"Set {len(translations)} translations for language '{language}'. Total languages: {len(TRANSLATIONS)}"
    
    except Exception as e:
        return f"Error setting translations: {str(e)}"

@command()
async def get_translations(language: str = None, context=None):
    """
    Get translations for a specific language or all languages.
    
    Args:
        language: Language code to get translations for (optional)
        context: Command context (optional)
    
    Returns:
        Dictionary of translations for the language, or all translations if no language specified
    
    Examples:
        # Get Spanish translations
        spanish_translations = await get_translations('es')
        
        # Get all translations
        all_translations = await get_translations()
    """
    try:
        if language:
            return TRANSLATIONS.get(language, {})
        else:
            return TRANSLATIONS
    
    except Exception as e:
        return f"Error getting translations: {str(e)}"

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
            for file_path in LOCALIZED_FILES_DIR.rglob("*.i18n.*"):
                localized_files.append(str(file_path.relative_to(LOCALIZED_FILES_DIR)))
        
        return {
            "count": len(localized_files),
            "files": sorted(localized_files)
        }
    
    except Exception as e:
        return f"Error listing localized files: {str(e)}"

def replace_placeholders(content: str, language: str) -> str:
    """
    Replace __TRANSLATE_key__ placeholders with actual translations.
    
    This function is used by the monkey-patch system to replace placeholders
    with actual translated text before serving templates.
    
    Args:
        content: Template content with placeholders
        language: Language code for translations
    
    Returns:
        Content with placeholders replaced by translations
    """
    if language not in TRANSLATIONS:
        return content
    
    translations = TRANSLATIONS[language]
    
    def replace_match(match):
        key = match.group(1)
        return translations.get(key, match.group(0))  # Return original if no translation
    
    # Replace all __TRANSLATE_key__ patterns
    return re.sub(r'__TRANSLATE_([a-z0-9_]+)__', replace_match, content)
