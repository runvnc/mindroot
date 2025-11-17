import os
import re
from pathlib import Path
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.types import Scope, Receive, Send
import sys
import traceback
try:
    from mindroot.coreplugins.l8n.utils import replace_placeholders, extract_plugin_root, get_localized_file_path, load_plugin_translations
    from mindroot.coreplugins.l8n.middleware import get_request_language
    from mindroot.coreplugins.l8n.language_detection import get_fallback_language
    L8N_AVAILABLE = True
except ImportError as e:
    trace = traceback.format_exc()
    L8N_AVAILABLE = False
    sys.exit(1)

class TranslatedStaticFiles(StaticFiles):
    """Custom StaticFiles handler that applies l8n translations to JavaScript files."""

    def __init__(self, *, directory: str, plugin_name: str=None, **kwargs):
        super().__init__(directory=directory, **kwargs)
        self.plugin_name = plugin_name
        self.directory_path = Path(directory)

    def get_current_language(self, request: Request) -> str:
        """Get the current language for the request."""
        if not L8N_AVAILABLE:
            return 'en'
        try:
            if hasattr(request.state, 'language'):
                return request.state.language
            lang = get_request_language()
            return get_fallback_language(lang) if lang else 'en'
        except Exception as e:
            return 'en'

    def should_translate_file(self, file_path: Path) -> bool:
        """Check if a file should be translated."""
        if not L8N_AVAILABLE:
            return False
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
            translated_content = replace_placeholders(content, language, file_path)
            if translated_content is None:
                return None
            return translated_content
        except Exception as e:
            return None

    async def get_response(self, path: str, scope: Scope) -> Response:
        """Override to add translation support for JavaScript files."""
        try:
            full_path = self.directory_path / path
            if full_path.exists() and self.should_translate_file(full_path):
                request = Request(scope)
                current_language = self.get_current_language(request)
                localized_path = get_localized_file_path(str(full_path))
                if localized_path.exists():
                    with open(localized_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    translated_content = self.apply_translations_to_js(content, current_language, str(localized_path))
                    if translated_content is not None:
                        return Response(content=translated_content, media_type='application/javascript', headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'})
            return await super().get_response(path, scope)
        except Exception as e:
            trace = traceback.format_exc()
            return await super().get_response(path, scope)

def mount_translated_static_files(app, plugin_name: str, category: str):
    """Mount plugin static files with translation support.
    
    Args:
        app (FastAPI): The FastAPI application instance
        plugin_name (str): Name of the plugin
        category (str): Plugin category ('core' or 'installed')
    """
    from .paths import get_plugin_path
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
        app.mount(f'/{dir_name}/static', TranslatedStaticFiles(directory=static_path, plugin_name=plugin_name), name=f'/{dir_name}/static')

def create_js_translation_object(translations: dict) -> str:
    """Create a JavaScript object containing translations.
    
    This can be injected into JS files to provide client-side translation support.
    
    Args:
        translations: Dictionary of translation key-value pairs
        
    Returns:
        JavaScript code defining a translation object
    """
    import json
    js_translations = json.dumps(translations, ensure_ascii=False)
    return f'\n// Auto-generated translation object\nwindow.MINDROOT_TRANSLATIONS = {js_translations};\n\n// Helper function to get translations\nwindow.translate = function(key, fallback) {{\n    return window.MINDROOT_TRANSLATIONS[key] || fallback || key;\n}};\n\n// Alias for shorter usage\nwindow.t = window.translate;\n'

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
    return translation_js + '\n\n' + content