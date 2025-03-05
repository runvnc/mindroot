"""Parent template environment with single template per filename."""
import os
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
from .plugins import list_enabled, get_plugin_path


class FirstMatchLoader(ChoiceLoader):
    """Custom loader that only returns the first matching template."""
    
    def __init__(self, loaders):
        super().__init__(loaders)
        self._template_cache = {}

    def get_source(self, environment, template):
        """Get template source, returning only first match for each template name."""
        if template in self._template_cache:
            return self._template_cache[template]

        # Try each loader until we find the first match
        for loader in self.loaders:
            try:
                source = loader.get_source(environment, template)
                self._template_cache[template] = source
                return source
            except Exception:
                continue
                
        # If we get here, no loader could find the template
        raise TemplateNotFound(template)


def get_parent_templates_env(plugins=None):
    """Set up Jinja2 environment that only loads first matching template.
    
    Args:
        plugins (list, optional): List of plugin names. Defaults to enabled plugins.
    
    Returns:
        Environment: Configured Jinja2 environment with FirstMatchLoader
    """
    if plugins is None:
        plugins = list_enabled(False)

    template_paths = []  # Use list to maintain order
    
    # Add plugin template paths in priority order
    for plugin in plugins:
        plugin_path = get_plugin_path(plugin)
        if not plugin_path:
            continue
            
        # Add main template directory
        template_dir = os.path.join(plugin_path, 'templates')
        if os.path.exists(template_dir):
            template_paths.append(template_dir)
            
        # Add parent directories to handle absolute paths
        # if it doesn't already exist in the list
        if os.path.dirname(plugin_path) not in template_paths:
            template_paths.append(os.path.dirname(plugin_path))
        if os.path.dirname(os.path.dirname(plugin_path)) not in template_paths:
            template_paths.append(os.path.dirname(os.path.dirname(plugin_path)))
    
    # Add default templates directory last
    template_paths.append('templates')

    print("**************************************************************************************")
    print("Loading templates from:", template_paths)

    # Create environment with FirstMatchLoader
    loaders = [FileSystemLoader(path) for path in template_paths]
    env = Environment(loader=FirstMatchLoader(loaders))
    
    return env
