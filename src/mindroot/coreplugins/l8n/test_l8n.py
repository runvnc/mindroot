"""
Simple test script for the l8n localization plugin.

This script tests the basic functionality of the localization commands
without requiring the full MindRoot environment.
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mod import write_localized_file, append_localized_file, set_translations, get_translations, list_localized_files, replace_placeholders

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
if __name__ == '__main__':
    asyncio.run(test_basic_functionality())