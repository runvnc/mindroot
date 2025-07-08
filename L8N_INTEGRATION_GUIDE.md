# MindRoot L8n Integration Guide

This guide explains how the l8n (localization) system has been integrated into MindRoot's template and static file serving systems.

## Overview

The l8n system provides translation support for:
1. **Jinja2 Templates** - HTML templates with `__TRANSLATE_key__` placeholders
2. **Static JavaScript Files** - JS files with translation placeholders
3. **Plugin Integration** - Automatic translation support for all plugins

## Key Changes Made

### 1. Template System Integration (`lib/templates.py`)

**What was changed:**
- Added l8n imports and availability checking
- Created `apply_translations_to_content()` function
- Modified `load_plugin_templates()` to use `load_template_with_translation()`
- Added `check_for_localized_template()` to find `.i18n.` versions
- Updated `render_direct_template()` with translation support

**How it works:**
- When loading templates, the system first checks for localized versions (`.i18n.` files)
- If found, loads the localized template and applies translations based on current language
- Falls back to original templates if no localized version exists
- Uses the l8n middleware to detect current language from request

### 2. Static File Translation (`lib/plugins/l8n_static_handler.py`)

**New custom static file handler:**
- `TranslatedStaticFiles` class extends FastAPI's `StaticFiles`
- Intercepts JavaScript file requests (`.js`, `.mjs`)
- Applies translations to JS files containing `__TRANSLATE_key__` placeholders
- Provides client-side translation helpers

**Features:**
- Automatic translation of JS files
- Language detection from request context
- Proper JavaScript string escaping
- Client-side translation object injection
- Fallback to regular file serving for non-JS files

### 3. Plugin Loader Updates (`lib/plugins/loader.py`)

**Integration points:**
- Modified `mount_static_files()` to use translated static handler when available
- Graceful fallback to regular static files if l8n is not available
- Automatic detection of l8n system availability

## Usage Guide

### 1. Creating Localized Templates

```python
# Use the l8n commands to create localized templates
await write_localized_file(
    "/path/to/original/template.jinja2",
    "<h1>__TRANSLATE_page_title__</h1><p>__TRANSLATE_welcome_message__</p>"
)
```

### 2. Setting Translations

```python
# Set translations for different languages
await set_translations(
    "/path/to/original/template.jinja2",
    'es',
    {
        'page_title': 'Título de la Página',
        'welcome_message': 'Mensaje de Bienvenida'
    }
)
```

### 3. JavaScript Translation

**In your JS files:**
```javascript
// Use translation placeholders in JavaScript
const messages = {
    loading: '__TRANSLATE_js_loading__',
    error: '__TRANSLATE_js_error__',
    success: '__TRANSLATE_js_success__'
};

// The system will replace these with actual translations
console.log(messages.loading); // Becomes "Loading..." or "Cargando..."
```

**Set JS translations:**
```python
await set_translations(
    "/path/to/script.js",
    'es',
    {
        'js_loading': 'Cargando...',
        'js_error': 'Error',
        'js_success': 'Éxito'
    }
)
```

### 4. Language Detection

The system automatically detects language from:
1. URL parameter: `?lang=es`
2. Cookie: `mindroot_language`
3. Accept-Language header
4. Environment variable: `MINDROOT_LANGUAGE`
5. Default: `en`

## File Structure

Localized files are stored in the l8n plugin directory:

```
l8n/
├── localized_files/          # Localized template versions
│   ├── coreplugins/
│   │   ├── chat/
│   │   │   └── templates/
│   │   │       └── chat.i18n.jinja2
│   │   └── admin/
│   │       └── templates/
│   │           └── admin.i18n.jinja2
│   └── external_plugins/
└── translations/             # Translation JSON files
    ├── coreplugins/
    │   ├── chat/
    │   │   └── translations.json
    │   └── admin/
    │       └── translations.json
    └── external_plugins/
```

## Translation Placeholder Rules

**Format:** `__TRANSLATE_key_name__`

**Rules:**
- Must start with `__TRANSLATE_` and end with `__`
- Use lowercase letters, numbers, and underscores only
- Use descriptive, hierarchical names
- Examples: `chat_title`, `buttons_send`, `nav_home`

## Testing

Run the integration test:

```bash
python /files/mindroot/test_l8n_integration.py
```

This will:
1. Create sample localized templates
2. Set translations for multiple languages
3. Create JavaScript files with translation placeholders
4. Test the translation system

## Client-Side JavaScript Helpers

The static file handler automatically injects translation helpers:

```javascript
// Available globally after JS file processing
window.MINDROOT_TRANSLATIONS = { /* translation object */ };

// Helper functions
window.translate('key', 'fallback');
window.t('key', 'fallback'); // Short alias
```

## Advantages of This Approach

1. **No Monkey Patching** - Integrates directly into the template system
2. **Plugin Compatible** - Works with all existing plugins
3. **Graceful Fallback** - System works even if l8n is not available
4. **Static File Support** - Translates JavaScript files automatically
5. **Performance** - Translations are applied at request time
6. **Flexible** - Supports both template and static file translation

## Troubleshooting

### Templates Not Translating
1. Check if l8n plugin is enabled
2. Verify localized template exists (`.i18n.` version)
3. Check translation JSON files are properly formatted
4. Ensure middleware is detecting language correctly

### JavaScript Files Not Translating
1. Verify static file handler is being used
2. Check file extension is `.js` or `.mjs`
3. Ensure translation placeholders follow correct format
4. Check browser network tab for proper content-type

### Language Not Detected
1. Check middleware is loaded and running
2. Test with explicit `?lang=es` URL parameter
3. Verify Accept-Language header is being sent
4. Check environment variables

## Future Enhancements

1. **CSS Translation** - Extend to CSS files for RTL languages
2. **Image Localization** - Support for localized images
3. **Caching** - Add translation caching for performance
4. **Hot Reload** - Live translation updates during development
5. **Validation** - Translation key validation and missing key detection

## Migration from Monkey Patch

If you were using the previous monkey patch system:

1. The monkey patch is disabled (has early return)
2. Templates now use the integrated system automatically
3. No code changes needed for existing templates
4. JavaScript translation is now supported
5. Better error handling and debugging

The new system provides the same functionality with better integration and additional features.
