from pathlib import Path
import os

L8N_AVAILABLE = True

# Base directory for l8n plugin
L8N_DIR = Path(os.environ.get('MR_SOURCE_DIR', '/files/mindroot/src/mindroot/coreplugins/l8n'))

# Base directory for localized files
LOCALIZED_FILES_DIR = L8N_DIR / "localized_files"

# Base directory for translations
TRANSLATIONS_DIR = L8N_DIR / "translations"

# Global cache for translations
# Structure: {plugin_path: {language: {key: translation}}}
TRANSLATIONS = {}


