import os
from jinja2 import Environment, FileSystemLoader

# Create a Jinja2 environment
env = Environment(loader=FileSystemLoader('.'))

# New helper function to find parent templates in plugins
async def find_parent_template(page_name, plugins):
    for plugin in plugins:
        template_path = os.path.join(plugin, 'templates', f'{page_name}.jinja2')
        if os.path.exists(template_path):
            return template_path
    return None

# Function to load templates from plugins
async def load_plugin_templates(page_name, plugins):
    templates = []
    for plugin in plugins:
        template_path = os.path.join(plugin, 'inject', f'{page_name}.jinja2')
        if os.path.exists(template_path):
            with open(template_path) as f:
                templates.append({'type': 'inject', 'template': env.from_string(f.read())})
        template_path2 = os.path.join(plugin, 'override', f'{page_name}.jinja2')
        if os.path.exists(template_path2):
            with open(template_path2) as f:
                templates.append({'type': 'override', 'template': env.from_string(f.read())})
        # Check for parent template in plugin's templates subdirectory
        parent_template_path = find_parent_template(page_name, plugins)
        if parent_template_path:
            with open(parent_template_path) as f:
                templates.append({'type': 'parent', 'template': env.from_string(f.read())})
    return templates

# Function to collect content from child templates
async def collect_content(template, blocks, template_type):
    content = {block: {'inject': [], 'override': None} for block in blocks}
    for block in blocks:
        if block in template.blocks:
            block_content = ''.join(template.blocks[block](template.new_context()))
            if template_type == 'override':
                content[block]['override'] = block_content
            else:
                content[block]['inject'].append(block_content)
    return content

# Function to render the combined template
async def render_combined_template(page_name, plugins, context):
    # Find parent template in plugins
    parent_template_path = await find_parent_template(page_name, plugins)
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

    for child_template_info in child_templates:
        child_content = await collect_content(child_template_info['template'], parent_blocks, child_template_info['type'])
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
            combined_template_str += f'{{% block {block} %}}\n    {{{{ combined_{block}_inject|safe }}}}\n{{% endblock %}}\n'

    combined_child_template = env.from_string(combined_template_str)

    # Render the combined child template with the parent template
    rendered_html = combined_child_template.render(
        layout_template=parent_template,
        **{f'combined_{block}_inject': ''.join(content['inject']) for block, content in all_content.items()},
        **{f'combined_{block}_override': content['override'] for block, content in all_content.items() if content['override']},
        **context
    )

    return rendered_html
