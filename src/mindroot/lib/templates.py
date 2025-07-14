import os
import logging
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
from .plugins import list_enabled, get_plugin_path
from .parent_templates import get_parent_templates_env
import traceback
import sys

# Import l8n translation functions
try:
    from mindroot.coreplugins.l8n.utils import replace_placeholders, get_localized_file_path, extract_plugin_root
    from mindroot.coreplugins.l8n.mod import *
    from mindroot.coreplugins.l8n.middleware import get_request_language
    from mindroot.coreplugins.l8n.language_detection import get_fallback_language
    L8N_AVAILABLE = True
except ImportError as e:
    trace = traceback.format_exc()
    print(f"L8n not available: {e} \n{trace}")
    L8N_AVAILABLE = False
    sys.exit(1)

# TODO: get_parent_templates_env(plugins):
# jinja2 environment containing only 1 template per plugin file name,
# the first one that is found from plugins with that name,
# need to look at how jinja2 loaders work

def get_current_language():
    """Get the current language for translation."""
    if not L8N_AVAILABLE:
        return 'en'
    
    try:
        # Try to get language from request context
        lang = get_request_language()
        return get_fallback_language(lang) if lang else 'en'
    except Exception as e:
        print(f"Error getting current language: {e}")
        return 'en'

def apply_translations_to_content(content, template_path=None):
    """Apply l8n translations to template content.
    
    Args:
        content (str): Template content with __TRANSLATE_key__ placeholders
        template_path (str): Path to the template file for plugin context
        
    Returns:
        str or None: Content with translations applied, or None if translations are incomplete
    """
    if not L8N_AVAILABLE or not content:
        return content
    
    try:
        current_language = get_current_language()
        
        # If we have a template path, use it for plugin context
        if template_path:
            # Check if translation failed (missing translations)
            translated = replace_placeholders(content, current_language, template_path)
            if translated is None:
                return None  # Signal that translations are incomplete
            return translated
        else:
            # Fallback: try to replace without plugin context
            return replace_placeholders(content, current_language)
    except Exception as e:
        print(f"Error applying translations: {e}")
        return content

def check_for_localized_template(template_path):
    """Check if a localized version of a template exists.
    
    Args:
        template_path (str): Original template path
        
    Returns:
        str: Path to localized template if it exists, None otherwise
    """
    if not L8N_AVAILABLE:
        return None
        
    try:
        localized_path = get_localized_file_path(template_path)
        if localized_path.exists():
            return str(localized_path)
    except Exception as e:
        print(f"Error checking for localized template: {e}")
    
    return None

def load_template_with_translation(template_path):
    """Load a template and apply translations if available and complete.
    
    If translations are missing for the current language, this function
    will fall back to serving the original template to avoid showing
    __TRANSLATE_key__ placeholders to users.
    
    Args:
        template_path (str): Path to the template file
        
    Returns:
        str: Template content with translations applied, or original content
             if translations are incomplete for the current language
    """
    # First check for localized version
    localized_path = check_for_localized_template(template_path)
    
    if localized_path:
        # Load localized template and apply translations
        try:
            with open(localized_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply translations - if None is returned, translations are incomplete
            translated_content = apply_translations_to_content(content, localized_path)
            if translated_content is None:
                # Fall back to original template
                print(f"L8n: Falling back to original template due to missing translations: {template_path}")
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return translated_content
        except Exception as e:
            print(f"Error loading localized template {localized_path}: {e}")
    
    # Fallback to original template
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content  # Don't apply translations to original templates
    except Exception as e:
        print(f"Error loading template {template_path}: {e}")
        return ""

def setup_template_environment(plugins=None):
    """Set up Jinja2 environment with multiple template paths.
    
    Returns:
        Environment: Configured Jinja2 environment
    """
    if plugins is None:
        plugins = list_enabled(False)
    template_paths = set(['templates'])  # Start with default templates directory
    
    # Add plugin template paths
    for plugin in plugins:
        plugin_path = get_plugin_path(plugin)
        if plugin_path:
            # Add main template directory
            template_dir = os.path.join(plugin_path, 'templates')
            if os.path.exists(template_dir):
                template_paths.add(template_dir)
                print(f"Added template path: {template_dir}")
            
            # Add inject directory
            inject_dir = os.path.join(plugin_path, 'inject')
            if os.path.exists(inject_dir):
                template_paths.add(inject_dir)
                # change color to green background, white text
                print("\033[92m" + f"Added inject path: {inject_dir}")
                # reset color
                print("\033[0m")

            # Add parent directories to handle absolute paths
            template_paths.add(os.path.dirname(plugin_path))
            template_paths.add(os.path.dirname(os.path.dirname(plugin_path)))
    
    # Create environment with multiple loaders
    loaders = [FileSystemLoader(path) for path in template_paths]
    env = Environment(loader=ChoiceLoader(loaders))
    print(f"Initialized Jinja2 environment with paths: {template_paths}")
    return env

# Create a Jinja2 environment with multiple template paths
env = setup_template_environment()
coreplugins =['admin', 'index', 'chat', 'chat_avatar', 'agent', 'jwt_auth', 'home', 'login', 'persona', 'events', 'user_service', 'usage', 'subscriptions', 'credits', 'startup']
parent_env = get_parent_templates_env(coreplugins)


async def find_parent_template(page_name, plugins):
    """Find parent template in enabled plugins.
    
    Args:
        page_name (str): Name of the template page
        plugins (list): List of enabled plugins
        
    Returns:
        str: Template path if found, None otherwise
    """
    for plugin in plugins:
        plugin_path = get_plugin_path(plugin)
        if not plugin_path:
            print(f'Warning: Could not find path for plugin: {plugin}')
            continue
            
        print(f'Checking plugin: {plugin}, path: {plugin_path}')
        template_path = os.path.join(plugin_path, 'templates', f'{page_name}.jinja2')
        
        if os.path.exists(template_path):
            print(f'Found parent template in plugin: {template_path}')
            # Convert to relative path from one of our template roots
            for loader in env.loader.loaders:
                for template_dir in loader.searchpath:
                    rel_path = os.path.relpath(template_path, template_dir)
                    if not rel_path.startswith('..'):
                        print(f'Using template path: {rel_path}')
                        return rel_path
            # Fallback to absolute path if no relative path works
            return template_path
        else:
            print(f'No parent template found in plugin: {plugin}, template path was {template_path}')
            
            # Try alternate locations
            alt_paths = [
                os.path.join(plugin_path, 'src', plugin, 'templates', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', 'templates', f'{page_name}.jinja2'),
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    print(f'Found parent template in alternate location: {alt_path}')
                    # Convert to relative path
                    for loader in env.loader.loaders:
                        for template_dir in loader.searchpath:
                            rel_path = os.path.relpath(alt_path, template_dir)
                            if not rel_path.startswith('..'):
                                print(f'Using template path: {rel_path}')
                                return rel_path
                    return alt_path
    return None
async def find_plugin_template(page_name, plugins):
    """Find a template in a plugin's templates directory.
    
    Args:
        page_name (str): Name of the template page
        plugins (list): List of enabled plugins
        
    Returns:
        tuple: (template_path, template_obj) if found, (None, None) otherwise
    """
    for plugin in plugins:
        plugin_path = get_plugin_path(plugin)
        if not plugin_path:
            print(f'Warning: Could not find path for plugin: {plugin}')
            continue
            
        # Try to find the template in the plugin's templates directory
        template_paths = [
            os.path.join(plugin_path, 'templates', f'{page_name}.jinja2'),
            os.path.join(plugin_path, 'src', plugin, 'templates', f'{page_name}.jinja2'),
            os.path.join(plugin_path, 'src', 'templates', f'{page_name}.jinja2'),
            os.path.join(plugin_path, 'src', plugin_path.split('/')[-1], 'templates', f'{page_name}.jinja2'),
        ]
        
        for path in template_paths:
            if os.path.exists(path):
                print(f'Found template in plugin: {path}')
                # Try to get the template from the environment
                try:
                    # Convert to relative path from one of our template roots
                    for loader in env.loader.loaders:
                        for template_dir in loader.searchpath:
                            rel_path = os.path.relpath(path, template_dir)
                            if not rel_path.startswith('..'):
                                template = env.get_template(rel_path)
                                return rel_path, template
                except Exception as e:
                    print(f'Error loading template: {e}')
    return None, None

async def load_plugin_templates(page_name, plugins):
    """Load templates from plugins with translation support.
    
    Args:
        page_name (str): Name of the template page
        plugins (list): List of enabled plugins
        
    Returns:
        list: List of template info dictionaries
    """
    templates = []
    for plugin in plugins:
        try:
            plugin_path = get_plugin_path(plugin)
            if not plugin_path:
                print(f'Warning: Could not find path for plugin: {plugin}')
                continue
 
            #print(f"Loading templates from plugin: {plugin}, path: {plugin_path}")
            # plugin might be name rather than directory
            # get the last part of the path to check also
            #
            last_part = plugin_path.split('/')[-1]
            # Check inject templates
            inject_paths = [
                os.path.join(plugin_path, 'inject', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', plugin, 'inject', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', 'inject', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', last_part, 'inject', f'{page_name}.jinja2'),
            ]
            
            for path in inject_paths:
                if os.path.exists(path):
                    # Load template content with translation support
                    content = load_template_with_translation(path)
                    if content:
                        #print(f"Found inject template at: {path}")
                        templates.append({'type': 'inject', 'template': env.from_string(content)})
                        break
                #else:
                #
                #    print(f"Inject template not found at: {path}")
            
            # Check override templates
            override_paths = [
                os.path.join(plugin_path, 'override', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', plugin, 'override', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', 'override', f'{page_name}.jinja2'),
                os.path.join(plugin_path, 'src', last_part, 'override', f'{page_name}.jinja2')
            ]
            
            for path in override_paths:
                if os.path.exists(path):
                    # Load template content with translation support
                    content = load_template_with_translation(path)
                    if content:
                        #print(f"Found override template at: {path}")
                        templates.append({'type': 'override', 'template': env.from_string(content)})
                        break
                        
        except Exception as e:
            print(f'Error loading plugin template: {e}')
            continue
    return templates

async def collect_content(template, blocks, template_type, data):
    """Collect content from child templates.
    
    Args:
        template: Jinja2 template object
        blocks (list): List of block names
        template_type (str): Type of template ('inject' or 'override')
        data (dict): Template context data
        
    Returns:
        dict: Collected content by block
    """
    content = {block: {'inject': [], 'override': None} for block in blocks}
    for block in blocks:
        if block in template.blocks:
            block_content = ''.join(template.blocks[block](template.new_context(data)))
 
            if template_type == 'override':
                content[block]['override'] = block_content
            else:
                content[block]['inject'].append(block_content)
    return content

async def render_combined_template(page_name, plugins, context):
    """Render combined template with injections and overrides, including translation support.
    
    Args:
        page_name (str): Name of the template page
        plugins (list): List of enabled plugins
        context (dict): Template context data (can be None)
        
    Returns:
        str: Rendered HTML
    """
    # Load parent template with translation support
    parent_template = None
    parent_template_path = None
    
    # Find the parent template file path
    # We need to search through the parent_env loaders to find the actual file
    for loader in parent_env.loader.loaders:
        for template_dir in loader.searchpath:
            potential_path = os.path.join(template_dir, f"{page_name}.jinja2")
            if os.path.exists(potential_path):
                parent_template_path = potential_path
                break
        if parent_template_path:
            break
    
    if parent_template_path:
        # Load the parent template with translation support
        parent_content = load_template_with_translation(parent_template_path)
        if parent_content:
            # Create a template object from the translated content
            parent_template = env.from_string(parent_content)
            # We need to preserve the original template name for Jinja2 inheritance
            parent_template.name = f"{page_name}.jinja2"
            parent_template.filename = parent_template_path
        else:
            # Fallback to loading without translation if something went wrong
            parent_template = parent_env.get_template(f"{page_name}.jinja2")
    else:
        # Fallback to original method if we can't find the file path
        parent_template = parent_env.get_template(f"{page_name}.jinja2")
    
    print(f"parent_template", parent_template)
    child_templates = await load_plugin_templates(page_name, plugins)
    parent_blocks = parent_template.blocks.keys()
    print(f"parent_blocks", parent_blocks)
    all_content = {block: {'inject': [], 'override': None} for block in parent_blocks}
    
    # Ensure context is a dictionary
    context = context or {}

    print("child_templates", child_templates)

    for child_template_info in child_templates:
        print("calling collect_content")
        child_content = await collect_content(
            child_template_info['template'],
            parent_blocks,
            child_template_info['type'],
            context
        )
        for block, content in child_content.items():
            if content['override']:
                all_content[block]['override'] = content['override']
            else:
                all_content[block]['inject'].extend(content['inject'])

    combined_template_str = '{% extends layout_template %}\n'
    for block in all_content:
        if all_content[block]['override']:
            combined_template_str += f'{{% block {block} %}}\n    {{{{ combined_{block}_override|safe }}}}\n{{% endblock %}}\n'
        else:
            combined_template_str += f'{{% block {block} %}}\n  {{{{ super() }}}}\n   {{{{ combined_{block}_inject|safe }}}}\n{{% endblock %}}\n'

    combined_child_template = env.from_string(combined_template_str)

    combined_inject = {}
    combined_override = {}

    for block, content in all_content.items():
        if 'inject' in content and isinstance(content['inject'], list):
            # print with a yellow background, black text
            # report details including page name and content injected
            print("\033[103m" + f"Injecting into block {block} on page {page_name} with content:")
            print(content['inject'])
            # reset color
            print("\033[0m")
            combined_inject[f'combined_{block}_inject'] = ''.join(content['inject'])
        else:
            combined_inject[f'combined_{block}_inject'] = ''

        if 'override' in content and content['override']:
            combined_override[f'combined_{block}_override'] = content['override']

    print("in render combined, context is", context)

    rendered_html = combined_child_template.render(
        layout_template=parent_template,
        **combined_inject,
        **combined_override,
        **context
    )

    return rendered_html

async def render_direct_template(template_path, context):
    """Render a template directly without combining with a parent template, with translation support.
    
    Args:
        template_path (str): Path to the template
        context (dict): Template context data
        
    Returns:
        str: Rendered HTML
    """
    # Ensure context is a dictionary
    context = context or {}
    
    try:
        # Check if we need to load with translation support
        template_full_path = None
        for loader in env.loader.loaders:
            for template_dir in loader.searchpath:
                potential_path = os.path.join(template_dir, template_path)
                if os.path.exists(potential_path):
                    template_full_path = potential_path
                    break
            if template_full_path:
                break
        
        if template_full_path:
            # Load with translation support
            content = load_template_with_translation(template_full_path)
            if content:
                template = env.from_string(content)
                return template.render(**context)
        
        # Fallback to normal template loading
        template = env.get_template(template_path)
        return template.render(**context)
    except Exception as e:
        logging.error(f"Error rendering template {template_path}: {e}")
        return f"<h1>Error rendering template</h1><p>{str(e)}</p>"

async def render(page_name, context):
    """Render a template with plugin injections, overrides, and translation support.
    If no parent template exists, tries to render a template directly from a plugin.
    
    Args:
        page_name (str): Name of the template page
        context (dict): Template context data (can be None)
        
    Returns:
        str: Rendered HTML
    """
    plugins = list_enabled(False)
    # print with white background red text
    # report details including page name and plugins enabled
    print("\033[101m" + f"Rendering page {page_name} with plugins enabled:")
    print(plugins)
    print("\033[0m")
    
    # Ensure context is a dictionary
    context = context or {}
    
    # First try to render with the combined template approach
    try:
        parent_env.get_template(f"{page_name}.jinja2")
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error finding parent template for {page_name}: {e}\n\n{trace}")
        print(f"No parent template found for {page_name}, trying direct rendering: {e}")
        
        # Try to find and render a template directly from a plugin
        template_path, _ = await find_plugin_template(page_name, plugins)
        if template_path:
            return await render_direct_template(template_path, context)
        
        return f"<h1>Template Not Found</h1><p>No template found for '{page_name}'</p>"

    try:
        return await render_combined_template(page_name, plugins, context)
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error rendering {page_name}: {e}\n\n{trace}")
        return f"<h1>Error Rendering Page</h1><p>{str(e)}</p><pre>{trace}</pre>"
