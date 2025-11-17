"""
Enhanced test script for the l8n localization plugin with language detection.
"""
import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from test_l8n_standalone import write_localized_file, set_translations, replace_placeholders, TRANSLATIONS
from language_detection import get_current_language_from_request, get_fallback_language, set_language_for_request, get_supported_languages, is_language_supported, _parse_accept_language_header

async def test_language_detection():
    """Test the enhanced language detection functionality."""
    default_lang = get_current_language_from_request()
    os.environ['MINDROOT_LANGUAGE'] = 'es'
    env_lang = get_current_language_from_request()
    supported = get_supported_languages()
    test_languages = ['es', 'fr', 'de', 'zh-cn', 'pt-br', 'invalid-lang']
    for lang in test_languages:
        fallback = get_fallback_language(lang)
        supported_check = is_language_supported(lang)
    test_headers = ['en-US,en;q=0.9,es;q=0.8,fr;q=0.7', 'es-ES,es;q=0.9,en;q=0.8', 'fr-FR,fr;q=0.9', 'de-DE,de;q=0.8,en;q=0.5', 'zh-CN,zh;q=0.9,en;q=0.1']
    for header in test_headers:
        parsed = _parse_accept_language_header(header)
    set_language_for_request('fr')
    current_lang = get_current_language_from_request()
    os.environ.pop('MINDROOT_LANGUAGE', None)

async def test_integrated_translation():
    """Test the integrated translation system with language detection."""
    await set_translations('en', {'welcome_title': 'Welcome to MindRoot', 'nav_home': 'Home', 'nav_settings': 'Settings', 'button_save': 'Save', 'button_cancel': 'Cancel'})
    await set_translations('es', {'welcome_title': 'Bienvenido a MindRoot', 'nav_home': 'Inicio', 'nav_settings': 'Configuración', 'button_save': 'Guardar', 'button_cancel': 'Cancelar'})
    await set_translations('fr', {'welcome_title': 'Bienvenue à MindRoot', 'nav_home': 'Accueil', 'nav_settings': 'Paramètres', 'button_save': 'Enregistrer', 'button_cancel': 'Annuler'})
    await set_translations('de', {'welcome_title': 'Willkommen bei MindRoot', 'nav_home': 'Startseite', 'nav_settings': 'Einstellungen', 'button_save': 'Speichern', 'button_cancel': 'Abbrechen'})
    template_content = '\n<html>\n<head>\n    <title>__TRANSLATE_welcome_title__</title>\n</head>\n<body>\n    <nav>\n        <a href="/">__TRANSLATE_nav_home__</a>\n        <a href="/settings">__TRANSLATE_nav_settings__</a>\n    </nav>\n    <main>\n        <h1>__TRANSLATE_welcome_title__</h1>\n        <div class="actions">\n            <button>__TRANSLATE_button_save__</button>\n            <button>__TRANSLATE_button_cancel__</button>\n        </div>\n    </main>\n</body>\n</html>\n'.strip()
    test_languages = ['en', 'es', 'fr', 'de', 'pt']
    for lang in test_languages:
        set_language_for_request(lang)
        fallback_lang = get_fallback_language(lang)
        translated = replace_placeholders(template_content, fallback_lang)
        title_line = [line for line in translated.split('\n') if '<title>' in line][0]
        h1_line = [line for line in translated.split('\n') if '<h1>' in line][0]

async def test_file_integration():
    """Test creating localized files and using language detection."""
    template_path = '/files/mindroot/src/mindroot/coreplugins/admin/templates/admin.jinja2'
    template_content = '\n<!DOCTYPE html>\n<html>\n<head>\n    <title>__TRANSLATE_admin_title__</title>\n</head>\n<body>\n    <header>\n        <h1>__TRANSLATE_admin_header__</h1>\n        <nav>\n            <a href="/admin/users">__TRANSLATE_nav_users__</a>\n            <a href="/admin/settings">__TRANSLATE_nav_settings__</a>\n            <a href="/admin/logs">__TRANSLATE_nav_logs__</a>\n        </nav>\n    </header>\n    <main>\n        <section>\n            <h2>__TRANSLATE_section_overview__</h2>\n            <p>__TRANSLATE_overview_description__</p>\n        </section>\n        <div class="actions">\n            <button class="primary">__TRANSLATE_button_create__</button>\n            <button class="secondary">__TRANSLATE_button_refresh__</button>\n        </div>\n    </main>\n</body>\n</html>\n'.strip()
    result = await write_localized_file(template_path, template_content)
    admin_translations = {'en': {'admin_title': 'MindRoot Administration', 'admin_header': 'Admin Dashboard', 'nav_users': 'Users', 'nav_settings': 'Settings', 'nav_logs': 'Logs', 'section_overview': 'System Overview', 'overview_description': 'Manage your MindRoot installation from this dashboard.', 'button_create': 'Create New', 'button_refresh': 'Refresh Data'}, 'es': {'admin_title': 'Administración de MindRoot', 'admin_header': 'Panel de Administración', 'nav_users': 'Usuarios', 'nav_settings': 'Configuración', 'nav_logs': 'Registros', 'section_overview': 'Resumen del Sistema', 'overview_description': 'Gestiona tu instalación de MindRoot desde este panel.', 'button_create': 'Crear Nuevo', 'button_refresh': 'Actualizar Datos'}, 'fr': {'admin_title': 'Administration MindRoot', 'admin_header': 'Tableau de Bord Admin', 'nav_users': 'Utilisateurs', 'nav_settings': 'Paramètres', 'nav_logs': 'Journaux', 'section_overview': 'Aperçu du Système', 'overview_description': 'Gérez votre installation MindRoot depuis ce tableau de bord.', 'button_create': 'Créer Nouveau', 'button_refresh': 'Actualiser les Données'}}
    for lang, translations in admin_translations.items():
        result = await set_translations(lang, translations)
    for lang in ['en', 'es', 'fr']:
        set_language_for_request(lang)
        current = get_current_language_from_request()
        fallback = get_fallback_language(current)
        translated = replace_placeholders(template_content, fallback)
        lines = translated.split('\n')
        title = next((line for line in lines if '<title>' in line), '').strip()
        header = next((line for line in lines if '<h1>' in line), '').strip()

async def main():
    """Run all enhanced tests."""
    await test_language_detection()
    await test_integrated_translation()
    await test_file_integration()
if __name__ == '__main__':
    asyncio.run(main())