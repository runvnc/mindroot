import os
import re
from pathlib import Path
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.types import Scope, Receive, Send
#from lib.utils.debug import debug_box
import sys
import traceback

# Import l8n translation functions
try:
    from mindroot.coreplugins.l8n.utils import replace_placeholders, extract_plugin_root, get_localized_file_path, load_plugin_translations
    from mindroot.coreplugins.l8n.middleware import get_request_language
    from mindroot.coreplugins.l8n.language_detection import get_fallback_language
    L8N_AVAILABLE = True
except ImportError as e:
    trace = traceback.format_exc()
    print(f"L8n not available for static files: {e}\n{trace}")
    L8N_AVAILABLE = False
    sys.exit(1)

class TranslatedStaticFiles(StaticFiles):
    """Custom StaticFiles handler that applies l8n translations to JavaScript files."""
    
    def __init__(self, *, directory: str, plugin_name: str = None, **kwargs):
        super().__init__(directory=directory, **kwargs)
        self.plugin_name = plugin_name
        self.directory_path = Path(directory)
    
    def get_current_language(self, request: Request) -> str:
        """Get the current language for the request."""
        print("Getting current language for static file request...")
        if not L8N_AVAILABLE:
            print("WARNING: L8n not available, defaulting to 'en'.")
            return 'en'
        
        try:
            # Try to get from request state first (set by middleware)
            if hasattr(request.state, 'language'):
                print(f"Using language from request state: {request.state.language}")
                return request.state.language
            
            # Fallback to l8n middleware function
            lang = get_request_language()
            return get_fallback_language(lang) if lang else 'en'
        except Exception as e:
            print(f"Error getting language for static file: {e}")
            return 'en'
    
    def should_translate_file(self, file_path: Path) -> bool:
        """Check if a file should be translated."""
        if not L8N_AVAILABLE:
            print("L8n not available, skipping translation check.")
            return False
        
        # show suffix
        print(f"Checking if file should be translated: {file_path} suffix is {file_path.suffix}")
        # Only translate JavaScript files for now
        return file_path.suffix.lower() in ['.js', '.mjs']
    
    def apply_translations_to_js(self, content: str, language: str, file_path: str) -> str:
        """Apply translations to JavaScript content.
        
        This looks for __TRANSLATE_key__ placeholders in JS files and replaces them
        with translated strings. If translations are missing, returns None to
        signal that the original file should be served instead.
        """
        if not L8N_AVAILABLE or not content:
            return content
        
        try:
            # Use the l8n replace_placeholders function
            translated_content = replace_placeholders(content, language, file_path)
            
            # If None is returned, translations are incomplete
            if translated_content is None:
                print(f"L8n: Missing translations for JS file, will serve original: {file_path}")
                return None
            
            return translated_content
        except Exception as e:
            print(f"Error applying translations to JS file {file_path}: {e}")
            return None  # Fallback to original file on error
    
    async def get_response(self, path: str, scope: Scope) -> Response:
        """Override to add translation support for JavaScript files."""
        try:
            # Get the full file path
            full_path = self.directory_path / path
            
            # Check if file exists and should be translated
            print(f"l8n Checking static file: {full_path}")
            if full_path.exists() and self.should_translate_file(full_path):
                print(f"l8n Translating static file: {full_path}")
                # Create a request object to get language
                request = Request(scope)
                current_language = self.get_current_language(request)
                print(f"[UPDATE] l8n Current language for static file: {current_language}")

                localized_path = get_localized_file_path(str(full_path))

                # Check if localized file exists
                if localized_path.exists():
                    # Read the localized file content
                    with open(localized_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Apply translations
                    translated_content = self.apply_translations_to_js(
                        content, current_language, str(localized_path)
                    )
                    
                    # If translations are complete, serve translated content
                    if translated_content is not None:
                        print(f"l8n: Serving translated JS file: {full_path}")
                        return Response(
                            content=translated_content,
                            media_type="application/javascript",
                            headers={
                                "Cache-Control": "no-cache, no-store, must-revalidate",
                                "Pragma": "no-cache",
                                "Expires": "0"
                            }
                        )
                    else:
                        print(f"l8n: Translations incomplete, serving original JS file: {full_path}")
                else:
                    print(f"l8n: No localized version found, serving original JS file: {full_path}")
            # For non-JS files or when translation is not available, use default behavior
            print(f"l8n Serving static file without translation: {full_path}")
            return await super().get_response(path, scope)
            
        except Exception as e:
            trace = traceback.format_exc()
            print(f"Error in translated static file handler: {e}\n{trace}")
            # Fallback to default behavior on error
            return await super().get_response(path, scope)

def mount_translated_static_files(app, plugin_name: str, category: str):
    """Mount plugin static files with translation support.
    
    Args:
        app (FastAPI): The FastAPI application instance
        plugin_name (str): Name of the plugin
        category (str): Plugin category ('core' or 'installed')
    """
    from .paths import get_plugin_path
    
    # debug_box(f"Mounting translated static files for plugin: {plugin_name} in category: {category}")

    plugin_dir = get_plugin_path(plugin_name)
    if not plugin_dir:
        return
        
    dir_name = os.path.basename(plugin_dir)
    
    if category != 'core': 
        static_path = os.path.join(plugin_dir, 'src', dir_name, 'static')
        if not os.path.exists(static_path):
            static_path = os.path.join(plugin_dir, 'static')
    else:
        static_path = os.path.join(plugin_dir, 'static')

    if os.path.exists(static_path):
        # Use our custom TranslatedStaticFiles instead of regular StaticFiles
        app.mount(
            f"/{dir_name}/static", 
            TranslatedStaticFiles(directory=static_path, plugin_name=plugin_name), 
            name=f"/{dir_name}/static"
        )
        print(f"Mounted translated static files for plugin: {plugin_name} at {static_path}")
        #debug_box(f"Mounted translated static files for plugin: {plugin_name} at {static_path}")
    else:
        print(f"No static files found for plugin: {plugin_name}. Searched in {static_path}")
        #debug_box(f"No static files found for plugin: {plugin_name}. Searched in {static_path}")

# JavaScript-specific translation helpers
def create_js_translation_object(translations: dict) -> str:
    """Create a JavaScript object containing translations.
    
    This can be injected into JS files to provide client-side translation support.
    
    Args:
        translations: Dictionary of translation key-value pairs
        
    Returns:
        JavaScript code defining a translation object
    """
    import json
    
    # Safely serialize translations to JavaScript
    js_translations = json.dumps(translations, ensure_ascii=False)
    
    return f"""
// Auto-generated translation object
window.MINDROOT_TRANSLATIONS = {js_translations};

// Helper function to get translations
window.translate = function(key, fallback) {{
    return window.MINDROOT_TRANSLATIONS[key] || fallback || key;
}};

// Alias for shorter usage
window.t = window.translate;
"""

def inject_translations_into_js(content: str, translations: dict) -> str:
    """Inject translation object into JavaScript content.
    
    This prepends translation definitions to JS files.
    
    Args:
        content: Original JavaScript content
        translations: Translation dictionary
        
    Returns:
        JavaScript content with translations injected
    """
    if not translations:
        return content
    
    translation_js = create_js_translation_object(translations)
    return translation_js + "\n\n" + content
