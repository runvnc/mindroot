#!/usr/bin/env python3
"""
Enhanced test script for the l8n localization plugin with language detection.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_l8n_standalone import (
    write_localized_file,
    set_translations,
    replace_placeholders,
    TRANSLATIONS
)

from language_detection import (
    get_current_language_from_request,
    get_fallback_language,
    set_language_for_request,
    get_supported_languages,
    is_language_supported,
    _parse_accept_language_header
)

async def test_language_detection():
    """Test the enhanced language detection functionality."""
    print("Testing Enhanced Language Detection...\n")
    
    # Test 1: Default language detection
    print("1. Testing default language detection...")
    default_lang = get_current_language_from_request()
    print(f"   Default language: {default_lang}")
    
    # Test 2: Environment variable override
    print("\n2. Testing environment variable override...")
    os.environ['MINDROOT_LANGUAGE'] = 'es'
    env_lang = get_current_language_from_request()
    print(f"   Language with MINDROOT_LANGUAGE=es: {env_lang}")
    
    # Test 3: Language fallback system
    print("\n3. Testing language fallback system...")
    supported = get_supported_languages()
    print(f"   Supported languages: {supported}")
    
    test_languages = ['es', 'fr', 'de', 'zh-cn', 'pt-br', 'invalid-lang']
    for lang in test_languages:
        fallback = get_fallback_language(lang)
        supported_check = is_language_supported(lang)
        print(f"   {lang} -> {fallback} (supported: {supported_check})")
    
    # Test 4: Accept-Language header parsing
    print("\n4. Testing Accept-Language header parsing...")
    test_headers = [
        'en-US,en;q=0.9,es;q=0.8,fr;q=0.7',
        'es-ES,es;q=0.9,en;q=0.8',
        'fr-FR,fr;q=0.9',
        'de-DE,de;q=0.8,en;q=0.5',
        'zh-CN,zh;q=0.9,en;q=0.1'
    ]
    
    for header in test_headers:
        parsed = _parse_accept_language_header(header)
        print(f"   '{header}' -> {parsed}")
    
    # Test 5: Set language for request
    print("\n5. Testing set_language_for_request...")
    set_language_for_request('fr')
    current_lang = get_current_language_from_request()
    print(f"   After setting to 'fr': {current_lang}")
    
    # Reset for next tests
    os.environ.pop('MINDROOT_LANGUAGE', None)
    
    print("\n✅ Language detection tests completed!")

async def test_integrated_translation():
    """Test the integrated translation system with language detection."""
    print("\nTesting Integrated Translation System...\n")
    
    # Set up translations for multiple languages
    print("1. Setting up translations...")
    
    # English (default)
    await set_translations('en', {
        'welcome_title': 'Welcome to MindRoot',
        'nav_home': 'Home',
        'nav_settings': 'Settings',
        'button_save': 'Save',
        'button_cancel': 'Cancel'
    })
    
    # Spanish
    await set_translations('es', {
        'welcome_title': 'Bienvenido a MindRoot',
        'nav_home': 'Inicio',
        'nav_settings': 'Configuración',
        'button_save': 'Guardar',
        'button_cancel': 'Cancelar'
    })
    
    # French
    await set_translations('fr', {
        'welcome_title': 'Bienvenue à MindRoot',
        'nav_home': 'Accueil',
        'nav_settings': 'Paramètres',
        'button_save': 'Enregistrer',
        'button_cancel': 'Annuler'
    })
    
    # German
    await set_translations('de', {
        'welcome_title': 'Willkommen bei MindRoot',
        'nav_home': 'Startseite',
        'nav_settings': 'Einstellungen',
        'button_save': 'Speichern',
        'button_cancel': 'Abbrechen'
    })
    
    print(f"   Set up translations for {len(TRANSLATIONS)} languages")
    
    # Test template with placeholders
    template_content = """
<html>
<head>
    <title>__TRANSLATE_welcome_title__</title>
</head>
<body>
    <nav>
        <a href="/">__TRANSLATE_nav_home__</a>
        <a href="/settings">__TRANSLATE_nav_settings__</a>
    </nav>
    <main>
        <h1>__TRANSLATE_welcome_title__</h1>
        <div class="actions">
            <button>__TRANSLATE_button_save__</button>
            <button>__TRANSLATE_button_cancel__</button>
        </div>
    </main>
</body>
</html>
""".strip()
    
    # Test translation for each language
    print("\n2. Testing translation for each language...")
    
    test_languages = ['en', 'es', 'fr', 'de', 'pt']  # pt should fallback to en
    
    for lang in test_languages:
        print(f"\n   Language: {lang}")
        
        # Set the language
        set_language_for_request(lang)
        
        # Get the fallback language
        fallback_lang = get_fallback_language(lang)
        print(f"   Fallback: {fallback_lang}")
        
        # Translate the template
        translated = replace_placeholders(template_content, fallback_lang)
        
        # Show a snippet of the translation
        title_line = [line for line in translated.split('\n') if '<title>' in line][0]
        h1_line = [line for line in translated.split('\n') if '<h1>' in line][0]
        
        print(f"   Title: {title_line.strip()}")
        print(f"   H1: {h1_line.strip()}")
    
    print("\n✅ Integrated translation tests completed!")

async def test_file_integration():
    """Test creating localized files and using language detection."""
    print("\nTesting File Integration...\n")
    
    # Create a localized template file
    print("1. Creating localized template file...")
    
    template_path = "/files/mindroot/src/mindroot/coreplugins/admin/templates/admin.jinja2"
    template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>__TRANSLATE_admin_title__</title>
</head>
<body>
    <header>
        <h1>__TRANSLATE_admin_header__</h1>
        <nav>
            <a href="/admin/users">__TRANSLATE_nav_users__</a>
            <a href="/admin/settings">__TRANSLATE_nav_settings__</a>
            <a href="/admin/logs">__TRANSLATE_nav_logs__</a>
        </nav>
    </header>
    <main>
        <section>
            <h2>__TRANSLATE_section_overview__</h2>
            <p>__TRANSLATE_overview_description__</p>
        </section>
        <div class="actions">
            <button class="primary">__TRANSLATE_button_create__</button>
            <button class="secondary">__TRANSLATE_button_refresh__</button>
        </div>
    </main>
</body>
</html>
""".strip()
    
    result = await write_localized_file(template_path, template_content)
    print(f"   {result}")
    
    # Set up admin-specific translations
    print("\n2. Setting up admin translations...")
    
    admin_translations = {
        'en': {
            'admin_title': 'MindRoot Administration',
            'admin_header': 'Admin Dashboard',
            'nav_users': 'Users',
            'nav_settings': 'Settings',
            'nav_logs': 'Logs',
            'section_overview': 'System Overview',
            'overview_description': 'Manage your MindRoot installation from this dashboard.',
            'button_create': 'Create New',
            'button_refresh': 'Refresh Data'
        },
        'es': {
            'admin_title': 'Administración de MindRoot',
            'admin_header': 'Panel de Administración',
            'nav_users': 'Usuarios',
            'nav_settings': 'Configuración',
            'nav_logs': 'Registros',
            'section_overview': 'Resumen del Sistema',
            'overview_description': 'Gestiona tu instalación de MindRoot desde este panel.',
            'button_create': 'Crear Nuevo',
            'button_refresh': 'Actualizar Datos'
        },
        'fr': {
            'admin_title': 'Administration MindRoot',
            'admin_header': 'Tableau de Bord Admin',
            'nav_users': 'Utilisateurs',
            'nav_settings': 'Paramètres',
            'nav_logs': 'Journaux',
            'section_overview': 'Aperçu du Système',
            'overview_description': 'Gérez votre installation MindRoot depuis ce tableau de bord.',
            'button_create': 'Créer Nouveau',
            'button_refresh': 'Actualiser les Données'
        }
    }
    
    for lang, translations in admin_translations.items():
        result = await set_translations(lang, translations)
        print(f"   {result}")
    
    # Test the complete workflow
    print("\n3. Testing complete localization workflow...")
    
    for lang in ['en', 'es', 'fr']:
        print(f"\n   Testing {lang.upper()} localization:")
        
        # Set language
        set_language_for_request(lang)
        current = get_current_language_from_request()
        fallback = get_fallback_language(current)
        
        # Translate template
        translated = replace_placeholders(template_content, fallback)
        
        # Extract and show key elements
        lines = translated.split('\n')
        title = next((line for line in lines if '<title>' in line), '').strip()
        header = next((line for line in lines if '<h1>' in line), '').strip()
        
        print(f"     Language: {current} -> Fallback: {fallback}")
        print(f"     {title}")
        print(f"     {header}")
    
    print("\n✅ File integration tests completed!")

async def main():
    """Run all enhanced tests."""
    print("=" * 60)
    print("MindRoot l8n Plugin - Enhanced Testing Suite")
    print("=" * 60)
    
    await test_language_detection()
    await test_integrated_translation()
    await test_file_integration()
    
    print("\n" + "=" * 60)
    print("✅ All enhanced tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
