import os
import logging
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
from .plugins import list_enabled, get_plugin_path
from .parent_templates import get_parent_templates_env
import traceback

# TODO: get_parent_templates_env(plugins):
# jinja2 environment containing only 1 template per plugin file name,
# the first one that is found from plugins with that name,
# need to look at how jinja2 loaders work

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
    """Load templates from plugins.
    
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
                    with open(path) as f:
                        #print(f"Found inject template at: {path}")
                        templates.append({'type': 'inject', 'template': env.from_string(f.read())})
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
                    with open(path) as f:
                        #print(f"Found override template at: {path}")
                        templates.append({'type': 'override', 'template': env.from_string(f.read())})
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
    """Render combined template with injections and overrides.
    
    Args:
        page_name (str): Name of the template page
        plugins (list): List of enabled plugins
        context (dict): Template context data (can be None)
        
    Returns:
        str: Rendered HTML
    """
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
    """Render a template directly without combining with a parent template.
    
    Args:
        template_path (str): Path to the template
        context (dict): Template context data
        
    Returns:
        str: Rendered HTML
    """
    # Ensure context is a dictionary
    context = context or {}
    
    try:
        template = env.get_template(template_path)
        return template.render(**context)
    except Exception as e:
        logging.error(f"Error rendering template {template_path}: {e}")
        return f"<h1>Error rendering template</h1><p>{str(e)}</p>"

async def render(page_name, context):
    """Render a template with plugin injections and overrides.
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

