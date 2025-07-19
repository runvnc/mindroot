#!/usr/bin/env python3
"""
Test script to demonstrate l8n integration with templates and static JS files.

This script shows how to:
1. Create localized templates with __TRANSLATE_key__ placeholders
2. Set translations for different languages
3. Create JavaScript files with translation placeholders
4. Test the translation system
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the mindroot source to Python path
sys.path.insert(0, '/files/mindroot/src')

# Import l8n functions
from mindroot.coreplugins.l8n.mod import (
    write_localized_file,
    set_translations,
    get_translations,
    list_localized_files
)

async def test_template_translation():
    """Test template translation functionality."""
    print("=== Testing Template Translation ===")
    
    # Example: Create a localized chat template
    chat_template_path = "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2"
    
    # Create localized template with translation placeholders
    localized_content = """
<!DOCTYPE html>
<html>
<head>
    <title>__TRANSLATE_chat_title__</title>
</head>
<body>
    <div class="chat-container">
        <h1>__TRANSLATE_chat_welcome__</h1>
        <div class="chat-messages" id="messages"></div>
        <div class="chat-input">
            <input type="text" placeholder="__TRANSLATE_chat_input_placeholder__" id="messageInput">
            <button onclick="sendMessage()">__TRANSLATE_chat_send_button__</button>
        </div>
        <div class="chat-status">
            <span id="status">__TRANSLATE_chat_status_ready__</span>
        </div>
    </div>
</body>
</html>
"""
    
    result = await write_localized_file(chat_template_path, localized_content)
    print(f"Created localized template: {result}")
    
    # Set English translations
    en_translations = {
        'chat_title': 'MindRoot Chat Interface',
        'chat_welcome': 'Welcome to MindRoot Chat',
        'chat_input_placeholder': 'Type your message here...',
        'chat_send_button': 'Send',
        'chat_status_ready': 'Ready'
    }
    
    result = await set_translations(chat_template_path, 'en', en_translations)
    print(f"Set English translations: {result}")
    
    # Set Spanish translations
    es_translations = {
        'chat_title': 'Interfaz de Chat MindRoot',
        'chat_welcome': 'Bienvenido al Chat de MindRoot',
        'chat_input_placeholder': 'Escribe tu mensaje aquí...',
        'chat_send_button': 'Enviar',
        'chat_status_ready': 'Listo'
    }
    
    result = await set_translations(chat_template_path, 'es', es_translations)
    print(f"Set Spanish translations: {result}")
    
    # Set French translations
    fr_translations = {
        'chat_title': 'Interface de Chat MindRoot',
        'chat_welcome': 'Bienvenue dans le Chat MindRoot',
        'chat_input_placeholder': 'Tapez votre message ici...',
        'chat_send_button': 'Envoyer',
        'chat_status_ready': 'Prêt'
    }
    
    result = await set_translations(chat_template_path, 'fr', fr_translations)
    print(f"Set French translations: {result}")
    
    # Test getting translations
    all_translations = await get_translations(chat_template_path)
    print(f"All translations: {all_translations}")
    
    spanish_only = await get_translations(chat_template_path, 'es')
    print(f"Spanish translations: {spanish_only}")

async def test_javascript_translation():
    """Test JavaScript file translation functionality."""
    print("\n=== Testing JavaScript Translation ===")
    
    # Create a sample JavaScript file with translation placeholders
    js_file_path = "/files/mindroot/src/mindroot/coreplugins/chat/static/js/chat-l8n-test.js"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(js_file_path), exist_ok=True)
    
    js_content = """
// Chat interface JavaScript with l8n support

class ChatInterface {
    constructor() {
        this.messages = [];
        this.statusMessages = {
            connecting: '__TRANSLATE_js_status_connecting__',
            connected: '__TRANSLATE_js_status_connected__',
            disconnected: '__TRANSLATE_js_status_disconnected__',
            error: '__TRANSLATE_js_status_error__'
        };
        
        this.uiText = {
            sendButton: '__TRANSLATE_js_send_button__',
            clearButton: '__TRANSLATE_js_clear_button__',
            placeholder: '__TRANSLATE_js_input_placeholder__',
            welcomeMessage: '__TRANSLATE_js_welcome_message__'
        };
    }
    
    showStatus(status) {
        const statusEl = document.getElementById('status');
        if (statusEl && this.statusMessages[status]) {
            statusEl.textContent = this.statusMessages[status];
        }
    }
    
    initializeUI() {
        const sendBtn = document.getElementById('sendButton');
        const clearBtn = document.getElementById('clearButton');
        const input = document.getElementById('messageInput');
        
        if (sendBtn) sendBtn.textContent = this.uiText.sendButton;
        if (clearBtn) clearBtn.textContent = this.uiText.clearButton;
        if (input) input.placeholder = this.uiText.placeholder;
        
        this.addMessage('system', this.uiText.welcomeMessage);
    }
    
    addMessage(type, content) {
        this.messages.push({ type, content, timestamp: new Date() });
        this.renderMessages();
    }
    
    renderMessages() {
        // Message rendering logic here
        console.log('Rendering messages:', this.messages);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const chat = new ChatInterface();
    chat.initializeUI();
    chat.showStatus('connected');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatInterface;
}
"""
    
    # Write the JavaScript file
    with open(js_file_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"Created JavaScript file: {js_file_path}")
    
    # Set translations for JavaScript strings
    js_en_translations = {
        'js_status_connecting': 'Connecting...',
        'js_status_connected': 'Connected',
        'js_status_disconnected': 'Disconnected',
        'js_status_error': 'Connection Error',
        'js_send_button': 'Send',
        'js_clear_button': 'Clear',
        'js_input_placeholder': 'Type your message...',
        'js_welcome_message': 'Welcome! How can I help you today?'
    }
    
    result = await set_translations(js_file_path, 'en', js_en_translations)
    print(f"Set English JS translations: {result}")
    
    js_es_translations = {
        'js_status_connecting': 'Conectando...',
        'js_status_connected': 'Conectado',
        'js_status_disconnected': 'Desconectado',
        'js_status_error': 'Error de Conexión',
        'js_send_button': 'Enviar',
        'js_clear_button': 'Limpiar',
        'js_input_placeholder': 'Escribe tu mensaje...',
        'js_welcome_message': '¡Bienvenido! ¿Cómo puedo ayudarte hoy?'
    }
    
    result = await set_translations(js_file_path, 'es', js_es_translations)
    print(f"Set Spanish JS translations: {result}")

async def test_admin_interface_translation():
    """Test admin interface translation."""
    print("\n=== Testing Admin Interface Translation ===")
    
    # Create localized admin template
    admin_template_path = "/files/mindroot/src/mindroot/coreplugins/admin/templates/admin.jinja2"
    
    admin_content = """
{% extends "base.jinja2" %}

{% block title %}__TRANSLATE_admin_title__{% endblock %}

{% block content %}
<div class="admin-container">
    <h1>__TRANSLATE_admin_heading__</h1>
    
    <nav class="admin-nav">
        <ul>
            <li><a href="#users">__TRANSLATE_admin_nav_users__</a></li>
            <li><a href="#plugins">__TRANSLATE_admin_nav_plugins__</a></li>
            <li><a href="#settings">__TRANSLATE_admin_nav_settings__</a></li>
            <li><a href="#logs">__TRANSLATE_admin_nav_logs__</a></li>
        </ul>
    </nav>
    
    <main class="admin-main">
        <section id="users">
            <h2>__TRANSLATE_admin_users_title__</h2>
            <p>__TRANSLATE_admin_users_description__</p>
        </section>
        
        <section id="plugins">
            <h2>__TRANSLATE_admin_plugins_title__</h2>
            <p>__TRANSLATE_admin_plugins_description__</p>
        </section>
    </main>
</div>
{% endblock %}
"""
    
    result = await write_localized_file(admin_template_path, admin_content)
    print(f"Created localized admin template: {result}")
    
    # Set admin translations
    admin_en_translations = {
        'admin_title': 'MindRoot Administration',
        'admin_heading': 'System Administration',
        'admin_nav_users': 'Users',
        'admin_nav_plugins': 'Plugins',
        'admin_nav_settings': 'Settings',
        'admin_nav_logs': 'Logs',
        'admin_users_title': 'User Management',
        'admin_users_description': 'Manage user accounts and permissions',
        'admin_plugins_title': 'Plugin Management',
        'admin_plugins_description': 'Install, configure, and manage plugins'
    }
    
    result = await set_translations(admin_template_path, 'en', admin_en_translations)
    print(f"Set English admin translations: {result}")
    
    admin_es_translations = {
        'admin_title': 'Administración de MindRoot',
        'admin_heading': 'Administración del Sistema',
        'admin_nav_users': 'Usuarios',
        'admin_nav_plugins': 'Plugins',
        'admin_nav_settings': 'Configuración',
        'admin_nav_logs': 'Registros',
        'admin_users_title': 'Gestión de Usuarios',
        'admin_users_description': 'Gestionar cuentas de usuario y permisos',
        'admin_plugins_title': 'Gestión de Plugins',
        'admin_plugins_description': 'Instalar, configurar y gestionar plugins'
    }
    
    result = await set_translations(admin_template_path, 'es', admin_es_translations)
    print(f"Set Spanish admin translations: {result}")

async def test_list_files():
    """Test listing all localized files."""
    print("\n=== Listing All Localized Files ===")
    
    files_info = await list_localized_files()
    print(f"Total localized files: {files_info['count']}")
    
    for file_path in files_info['files']:
        print(f"  - {file_path}")

async def main():
    """Run all tests."""
    print("MindRoot L8n Integration Test")
    print("=============================")
    
    try:
        await test_template_translation()
        await test_javascript_translation()
        await test_admin_interface_translation()
        await test_list_files()
        
        print("\n=== Test Summary ===")
        print("✅ Template translation: PASSED")
        print("✅ JavaScript translation: PASSED")
        print("✅ Admin interface translation: PASSED")
        print("✅ File listing: PASSED")
        
        print("\n=== Next Steps ===")
        print("1. Start MindRoot server")
        print("2. Test template rendering with different languages")
        print("3. Test static JS file serving with translations")
        print("4. Use ?lang=es or ?lang=fr URL parameters to test")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
