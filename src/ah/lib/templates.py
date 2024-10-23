import os
from jinja2 import Environment, FileSystemLoader
from .plugins import list_enabled, get_plugin_path

# Create a Jinja2 environment
env = Environment(loader=FileSystemLoader('.'))

# New helper function to find parent templates in plugins
async def find_parent_template(page_name, plugins):
    for plugin in plugins:
        plugin_path = get_plugin_path(plugin)
        print(f'Checking plugin: {plugin}, path: {plugin_path}')
        template_path = os.path.join(plugin_path, 'templates', f'{page_name}.jinja2')
        if os.path.exists(template_path):
            print(f'Found parent template in plugin: {template_path}')
            return template_path
        else:
            print(f'No parent template found in plugin: {plugin}, template path was {template_path}')
    return None

# Function to load templates from plugins
async def load_plugin_templates(page_name, plugins):
    templates = []
    for plugin in plugins:
        template_path = os.path.join('ah', plugin, 'inject', f'{page_name}.jinja2')
        if os.path.exists(template_path):
            with open(template_path) as f:
                print("Found inject template for page", page_name, "in plugin", plugin, "at", template_path)
                templates.append({'type': 'inject', 'template': env.from_string(f.read())})
        else:
            print("No inject template found for page", page_name, "in plugin", plugin, "at", template_path)

        template_path2 = os.path.join('ah', plugin, 'override', f'{page_name}.jinja2')
        if os.path.exists(template_path2):
            with open(template_path2) as f:
                templates.append({'type': 'override', 'template': env.from_string(f.read())})
    return templates

# Function to collect content from child templates
async def collect_content(template, blocks, template_type, data):
    content = {block: {'inject': [], 'override': None} for block in blocks}
    for block in blocks:
        if block in template.blocks:
            block_content = ''.join(template.blocks[block](template.new_context(data)))
 
            if template_type == 'override':
                content[block]['override'] = block_content
            else:
                content[block]['inject'].append(block_content)
    return content

# Function to render the combined template
async def render_combined_template(page_name, plugins, context):
    print("plugins:", plugins)
    # Find parent template in plugins
    parent_template_path = await find_parent_template(page_name, plugins)
    # print a green top border with ascii
    print("\033[92m" + "----------------------------------")
    print("parent_template_path", parent_template_path)
    print("page name", page_name, "plugins:", plugins, "context:", context)
    #back to normal text
    print("\033[0m")
    if parent_template_path:
        parent_template = env.get_template(parent_template_path)
    else:
        parent_template = env.get_template(f'templates/{page_name}.jinja2')

    # Load child templates from plugins
    child_templates = await load_plugin_templates(page_name, plugins)

    # Get the blocks defined in the parent template
    parent_blocks = parent_template.blocks.keys()

    # Collect content from child templates
    all_content = {block: {'inject': [], 'override': None} for block in parent_blocks}

    print("child_templates", child_templates)

    for child_template_info in child_templates:
        print("calling collect_content")
        child_content = await collect_content(child_template_info['template'], parent_blocks, child_template_info['type'], context)
        for block, content in child_content.items():
            if content['override']:
                all_content[block]['override'] = content['override']
            else:
                all_content[block]['inject'].extend(content['inject'])

    # Generate the combined template dynamically
    combined_template_str = '{% extends layout_template %}\n'
    for block in all_content:
        if all_content[block]['override']:
            combined_template_str += f'{{% block {block} %}}\n    {{{{ combined_{block}_override|safe }}}}\n{{% endblock %}}\n'
        else:
            print("injecting")
            combined_template_str += f'{{% block {block} %}}\n  {{{{ super() }}}}\n   {{{{ combined_{block}_inject|safe }}}}\n{{% endblock %}}\n'

    combined_child_template = env.from_string(combined_template_str)
    print("combined_template_str", combined_template_str)
    print("combined_child_template", combined_child_template)
    print("parent_template", parent_template)
    print("all_content", all_content)

    # Render the combined child template with the parent template
    # need to make sure all_content is not {} or None
    # Initialize the dictionaries
    combined_inject = {}
    combined_override = {}

    # Iterate through all_content items and populate the dictionaries with checks
    for block, content in all_content.items():
        # Check if 'inject' exists and is a list
        if 'inject' in content and isinstance(content['inject'], list):
            combined_inject[f'combined_{block}_inject'] = ''.join(content['inject'])
        else:
            combined_inject[f'combined_{block}_inject'] = ''  # Default to empty string if not present or not a list

        # Check if 'override' exists and is not None
        if 'override' in content and content['override']:
            combined_override[f'combined_{block}_override'] = content['override']

    print("in render combined, context is", context)

    # Render the template with the combined dictionaries and context
    rendered_html = combined_child_template.render(
        layout_template=parent_template,
        **combined_inject,
        **combined_override,
        **context
    )

    return rendered_html

async def render(page_name, context):
    plugins = list_enabled(False)
    return await render_combined_template(page_name, plugins, context)

