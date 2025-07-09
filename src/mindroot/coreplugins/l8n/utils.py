# need to import Path
from pathlib import Path
from .l8n_constants import *
import json
import re

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




def replace_placeholders(content: str, language: str, plugin_path: str = None) -> str:
    """
    Replace __TRANSLATE_key__ placeholders with actual translations.
    
    This function is used by the monkey-patch system to replace placeholders
    with actual translated text before serving templates.
    
    Args:
        content: Template content with placeholders
        language: Language code for translations
        plugin_path: Path to the localized file (used to determine which plugin's translations to use)
    
    Returns:
        Content with placeholders replaced by translations
    """
    if not plugin_path:
        # No plugin path provided, return content unchanged
        print("Warning: No plugin path provided for translation replacement.")
        return content
    
    try:
        # Extract plugin name from the localized file path
        # Path format: .../localized_files/[coreplugins|external_plugins]/[plugin_name]/...
        path_parts = Path(plugin_path).parts
        
        # Find 'localized_files' in the path
        if 'localized_files' in path_parts:
            print("1")
            idx = path_parts.index('localized_files')
            if idx + 2 < len(path_parts):
                # Get plugin name (should be at idx+2)
                plugin_type = path_parts[idx + 1]  # 'coreplugins' or 'external_plugins'
                plugin_name = path_parts[idx + 2]
                
                # Load translations for this plugin
                translations_path = TRANSLATIONS_DIR / plugin_type / plugin_name / "translations.json"
                print(f"Translations path: {translations_path}")
                plugin_translations = {}
                if translations_path.exists():
                    try:
                        with open(translations_path, 'r', encoding='utf-8') as f:
                             plugin_translations = json.load(f)
                    except Exception as e:
                        print(f"Warning: Could not load translations from {translations_path}: {e}")
                
                    print(f"Loaded translations for plugin: {plugin_name}: {plugin_translations}")
                    if language in plugin_translations:
                        print(f"Using translations for language: {language}")
                        # Replace placeholders
                        translations = plugin_translations[language]
                        
                        def replace_match(match):
                            key = match.group(1)
                            return translations.get(key, match.group(0))  # Return original if no translation
                        
                        return re.sub(r'__TRANSLATE_([a-z0-9_]+)__', replace_match, content)
                    else:
                        print(f"Warning: No translations found for language '{language}' in {translations_path}")
                else:
                    print(f"Warning: Translations file not found at {translations_path}")
        
        return content
    
    except Exception as e:
        print(f"Warning: Error in replace_placeholders: {e}")
        return content
       
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
            print(f"Warning: Could not load translations from {translations_file}: {e}")
    else:
        print(f"Warning: Translations file does not exist at {translations_file}")
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


