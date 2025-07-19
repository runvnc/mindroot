# MindRoot Localization Plugin (l8n)

A portable localization system for MindRoot that uses static placeholders and server-side replacement.

## Features

- **Portable**: Works regardless of installation directory
- **Non-destructive**: Original files remain untouched
- **Transparent**: Existing plugins work without modification
- **Static placeholders**: Uses `__TRANSLATE_key__` format
- **Automatic template interception**: Monkey-patches Jinja2 for seamless integration

## Commands

### write_localized_file(original_path, content)
Creates a localized version of a file with translation placeholders.

### append_localized_file(original_path, content)
Appends content to an existing localized file.

### set_translations(language, translations)
Sets translation mappings for a specific language.

### get_translations(language=None)
Retrieves translations for a language or all languages.

### list_localized_files()
Lists all created localized files.

## Placeholder Format

Use the format: `__TRANSLATE_key_name__`

**Rules:**
- Must start with `__TRANSLATE_` and end with `__`
- Use lowercase letters, numbers, and underscores only
- Use descriptive, hierarchical names like `section_element`

**Examples:**
- `__TRANSLATE_chat_title__` → "Chat Interface"
- `__TRANSLATE_buttons_send__` → "Send Message"
- `__TRANSLATE_nav_home__` → "Home"

## Usage Example

```python
# Create a localized template
await write_localized_file(
    "/files/mindroot/src/mindroot/coreplugins/chat/templates/chat.jinja2",
    "<h1>__TRANSLATE_chat_title__</h1><button>__TRANSLATE_buttons_send__</button>"
)

# Set Spanish translations
await set_translations('es', {
    'chat_title': 'Interfaz de Chat',
    'buttons_send': 'Enviar Mensaje'
})

# Set French translations
await set_translations('fr', {
    'chat_title': 'Interface de Chat',
    'buttons_send': 'Envoyer le Message'
})
```

## File Structure

Localized files are stored in `l8n/localized_files/` with the following structure:

```
localized_files/
├── coreplugins/
│   ├── chat/
│   │   └── templates/
│   │       └── chat.i18n.jinja2
│   └── admin/
│       └── templates/
│           └── admin.i18n.jinja2
└── external_plugins/
    └── my_plugin/
        └── templates/
            └── page.i18n.jinja2
```

## How It Works

1. **Template Interception**: Monkey-patches Jinja2's FileSystemLoader to intercept template loading
2. **Localized File Detection**: Searches for `.i18n.` versions of requested templates
3. **Placeholder Replacement**: Replaces `__TRANSLATE_key__` with actual translations based on current language
4. **Fallback**: Uses original templates if no localized version exists

## Language Detection

Currently defaults to English ('en'). Future versions will support:
- HTTP Accept-Language headers
- User preferences from database
- URL parameters (?lang=es)
- Cookie values

## Path Matching

Uses intelligent path matching to find templates regardless of installation directory:
1. Exact filename match
2. Match last 2 path components
3. Match last 3 path components

This ensures the system works across different server setups and installation paths.
