# need to import Path
from pathlib import Path
from .l8n_constants import *
import json
import re
import logging

# Set up logging for l8n warnings
logger = logging.getLogger('l8n')
logger.setLevel(logging.WARNING)

# Create console handler with formatting
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('\033[91m[L8N WARNING]\033[0m %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

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

def extract_translation_keys(content: str) -> set:
    """
    Extract all __TRANSLATE_key__ placeholders from content.
    
    Args:
        content: Content to scan for translation keys
        
    Returns:
        Set of translation keys found in the content
    """
    pattern = r'__TRANSLATE_([a-z0-9_]+)__'
    matches = re.findall(pattern, content)
    return set(matches)

def replace_placeholders(content: str, language: str, plugin_path: str = None) -> str:
    """
    Replace __TRANSLATE_key__ placeholders with actual translations.
    
    This function now validates that ALL required translations are available
    for the specified language. If any translations are missing, it logs
    a strong warning and returns None to indicate fallback is needed.
    
    Args:
        content: Template content with placeholders
        language: Language code for translations
        plugin_path: Path to the localized file (used to determine which plugin's translations to use)
    
    Returns:
        Content with placeholders replaced by translations, or None if translations are incomplete
    """
    if not plugin_path:
        # No plugin path provided, return content unchanged
        logger.warning("No plugin path provided for translation replacement.")
        return content
    
    try:
        # Extract all translation keys from the content
        required_keys = extract_translation_keys(content)
        
        if not required_keys:
            # No translation keys found, return content as-is
            return content
        
        # Extract plugin name from the localized file path
        # Path format: .../localized_files/[coreplugins|external_plugins]/[plugin_name]/...
        path_parts = Path(plugin_path).parts
        
        # Find 'localized_files' in the path
        if 'localized_files' in path_parts:
            idx = path_parts.index('localized_files')
            if idx + 2 < len(path_parts):
                # Get plugin name (should be at idx+2)
                plugin_type = path_parts[idx + 1]  # 'coreplugins' or 'external_plugins'
                plugin_name = path_parts[idx + 2]
                
                # Load translations for this plugin
                translations_path = TRANSLATIONS_DIR / plugin_type / plugin_name / "translations.json"
                plugin_translations = {}
                if translations_path.exists():
                    try:
                        with open(translations_path, 'r', encoding='utf-8') as f:
                             plugin_translations = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load translations from {translations_path}: {e}")
                        return None  # Fallback to original file
                
                if language in plugin_translations:
                    translations = plugin_translations[language]
                    
                    # Check if ALL required translations are available
                    missing_keys = required_keys - set(translations.keys())
                    
                    if missing_keys:
                        # Some translations are missing - log strong warning and return None
                        missing_list = ', '.join(sorted(missing_keys))
                        logger.warning(
                            f"\n" +
                            f"="*80 + "\n" +
                            f"MISSING TRANSLATIONS DETECTED!\n" +
                            f"Plugin: {plugin_name}\n" +
                            f"Language: {language}\n" +
                            f"File: {plugin_path}\n" +
                            f"Missing keys: {missing_list}\n" +
                            f"Falling back to original file to avoid showing placeholders.\n" +
                            f"="*80
                        )
                        return None  # Signal that fallback is needed
                    
                    # All translations are available - proceed with replacement
                    def replace_match(match):
                        key = match.group(1)
                        return translations.get(key, match.group(0))  # This shouldn't happen now
                    
                    return re.sub(r'__TRANSLATE_([a-z0-9_]+)__', replace_match, content)
                else:
                    # No translations for this language
                    logger.warning(
                        f"\n" +
                        f"="*80 + "\n" +
                        f"NO TRANSLATIONS FOR LANGUAGE!\n" +
                        f"Plugin: {plugin_name}\n" +
                        f"Language: {language}\n" +
                        f"File: {plugin_path}\n" +
                        f"Required keys: {', '.join(sorted(required_keys))}\n" +
                        f"Falling back to original file.\n" +
                        f"="*80
                    )
                    return None  # Signal that fallback is needed
            else:
                logger.warning(f"Could not extract plugin info from path: {plugin_path}")
                return None
        else:
            logger.warning(f"Path does not contain 'localized_files': {plugin_path}")
            return None
        
    except Exception as e:
        logger.warning(f"Error in replace_placeholders: {e}")
        return None  # Fallback to original file on any error
       
def get_localized_file_path(original_path: str) -> Path:
    """
    Convert an original file path to its localized version path.
    
    Examples:
    - chat/templates/chat.jinja2 -> localized_files/coreplugins/chat/templates/chat.i18n.jinja2
    - my_plugin/templates/page.jinja2 -> localized_files/external_plugins/my_plugin/templates/page.i18n.jinja2
    """
    plugin_root = extract_plugin_root(original_path)
    path = Path(plugin_root)
    
    # Determine if this is a core plugin or external plugin based on the absolute path
    if 'coreplugins' in original_path:
        base_dir = LOCALIZED_FILES_DIR / "coreplugins"
    else:
        base_dir = LOCALIZED_FILES_DIR / "external_plugins"
    
    # Add .i18n before the file extension
    stem = path.stem
    suffix = path.suffix
    new_filename = f"{stem}.i18n{suffix}"
    
    localized_path = base_dir / path.parent / new_filename
    return localized_path


def load_plugin_translations(plugin_path: str):
    """Load translations for a specific plugin from disk."""

    translations_file = get_plugin_translations_path(plugin_path)
    
    if translations_file.exists():
        try:
            with open(translations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load translations from {translations_file}: {e}")
    else:
        logger.warning(f"Translations file does not exist at {translations_file}")
    return {}

def get_plugin_translations_path(original_path: str) -> Path:
    """
    Get the path where translations should be stored for a given file.
    
    Example:
    /files/mindroot/src/mindroot/coreplugins/check_list/inject/admin.jinja2
    -> translations/coreplugins/check_list/translations.json
    """
    plugin_root = extract_plugin_root(original_path)
    
    # Determine if this is a core plugin or external plugin based on the absolute path
    if 'coreplugins' in original_path:
        base_dir = TRANSLATIONS_DIR / "coreplugins"
    else:
        base_dir = TRANSLATIONS_DIR / "external_plugins"
    
    # Get just the plugin name (first part of plugin_root)
    plugin_name = Path(plugin_root).parts[0]
    
    return base_dir / plugin_name / "translations.json"


