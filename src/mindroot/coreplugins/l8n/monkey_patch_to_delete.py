to_delete = """
import os
import re
from pathlib import Path
from typing import Optional

# Import the translation replacement function
from .mod import replace_placeholders, LOCALIZED_FILES_DIR

# Import the enhanced language detection
from .language_detection import get_fallback_language
from .middleware import get_request_language

# Store original Jinja2 loader methods
_original_get_source = None
_original_loader_get_source = None

def get_current_language() -> str:
    """
    Get the current language for the request using enhanced detection.
    """
    return get_fallback_language(get_request_language())

def find_localized_template(template_name: str) -> Optional[Path]:
    """
    Find a localized version of a template.
    
    Uses relative path matching to find templates regardless of installation directory.
    
    Args:
        template_name: Original template name/path
    
    Returns:
        Path to localized template if found, None otherwise
    """
    if not LOCALIZED_FILES_DIR.exists():
        return None
    
    # Convert template name to potential localized paths
    template_path = Path(template_name)
    stem = template_path.stem
    suffix = template_path.suffix
    
    # Create the .i18n version filename
    localized_filename = f"{stem}.i18n{suffix}"
    
    # Search strategies in order of preference:
    search_strategies = [
        # 1. Exact filename match anywhere in localized_files
        lambda: list(LOCALIZED_FILES_DIR.rglob(localized_filename)),
        
        # 2. Match last 2 path components
        lambda: _find_by_path_components(template_path, localized_filename, 2),
        
        # 3. Match last 3 path components
        lambda: _find_by_path_components(template_path, localized_filename, 3),
    ]
    
    for strategy in search_strategies:
        matches = strategy()
        if matches:
            # Return the first match
            return matches[0]
    
    return None

def _find_by_path_components(original_path: Path, localized_filename: str, num_components: int) -> list:
    """
    Find localized templates by matching the last N path components.
    
    Args:
        original_path: Original template path
        localized_filename: Localized filename to search for
        num_components: Number of path components to match
    
    Returns:
        List of matching paths
    """
    if len(original_path.parts) < num_components:
        return []
    
    # Get the last N-1 components (excluding filename) + localized filename
    target_components = original_path.parts[-(num_components-1):]
    target_path_pattern = '/'.join(target_components[:-1]) + '/' + localized_filename
    
    matches = []
    for candidate in LOCALIZED_FILES_DIR.rglob(localized_filename):
        candidate_relative = candidate.relative_to(LOCALIZED_FILES_DIR)
        if str(candidate_relative).endswith(target_path_pattern):
            matches.append(candidate)
    
    return matches

def patched_get_source(self, environment, template):
    """
    Patched version of Jinja2 loader's get_source method.
    
    This intercepts template loading and:
    1. Checks for localized versions
    2. Replaces placeholders with translations
    3. Falls back to original templates if no localized version exists
    """
    # First, try to find a localized version
    localized_path = find_localized_template(template)
    
    if localized_path and localized_path.exists():
        try:
            # Read the localized template
            with open(localized_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Replace placeholders with translations
            current_language = get_current_language()
            translated_source = replace_placeholders(source, current_language, str(localized_path))
            
            # Return the translated source
            # Note: We use the original template name for caching purposes
            return translated_source, str(localized_path), lambda: True
        
        except Exception as e:
            # If there's an error reading the localized template, fall back to original
            print(f"Error loading localized template {localized_path}: {e}")
    
    # Fall back to original template loading
    return _original_get_source(self, environment, template)

def install_monkey_patch():
    """
    Install the monkey patch for Jinja2 template loading.
    
    This patches the FileSystemLoader.get_source method to intercept
    template loading and provide localized versions when available.
    """
    global _original_get_source
    return
    try:
        from jinja2 import FileSystemLoader
        
        # Store the original method
        if _original_get_source is None:
            _original_get_source = FileSystemLoader.get_source
        
        # Install the patch
        FileSystemLoader.get_source = patched_get_source
        
        print("L8n monkey patch installed successfully")
        return True
    
    except ImportError:
        print("Warning: Could not import Jinja2 for monkey patching")
        return False
    except Exception as e:
        print(f"Error installing l8n monkey patch: {e}")
        return False

def uninstall_monkey_patch():
    """
    Remove the monkey patch and restore original Jinja2 behavior.
    """
    global _original_get_source
    
    try:
        from jinja2 import FileSystemLoader
        
        if _original_get_source is not None:
            FileSystemLoader.get_source = _original_get_source
            print("L8n monkey patch removed successfully")
            return True
        else:
            print("No monkey patch to remove")
            return False
    
    except ImportError:
        print("Warning: Could not import Jinja2 for monkey patch removal")
        return False
    except Exception as e:
        print(f"Error removing l8n monkey patch: {e}")
        return False

# Auto-install the monkey patch when this module is imported
# Prevent double installation by checking if already installed
if __name__ != '__main__' and not hasattr(install_monkey_patch, '_auto_installed'):
    install_monkey_patch()
    install_monkey_patch._auto_installed = True

"""
