from jinja2 import Template

markdown_template = '''
# Hello, {{ name }}!

Welcome to my Markdown template.

## About Me

I am a {{ occupation }} and I love {{ hobby }}.

## Favorite Programming Languages

{% for language in languages %}
- {{ language }}
{% endfor %}
'''

data = {
    'name': 'John Doe',
    'occupation': 'Software Engineer',
    'hobby': 'coding',
    'languages': ['Python', 'JavaScript', 'C++']
}

template = Template(markdown_template)
rendered_markdown = template.render(data)

print(rendered_markdown)
