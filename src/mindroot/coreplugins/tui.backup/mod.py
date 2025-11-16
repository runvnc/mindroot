\"\"\"MindRoot TUI Plugin - Provides the 'mr' command-line interface.\"\"\"

from lib.providers.hooks import hook
import os

print(\"--- MindRoot TUI Plugin Loaded ---\")

async def on_load(app):
    \"\"\"Called when the plugin is loaded.\"\"\"
    print(\"TUI plugin loaded - 'mr' command available\")
    pass
