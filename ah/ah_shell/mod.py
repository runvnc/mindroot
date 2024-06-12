import os
import subprocess
import fnmatch
from ..commands import command

@command()
async def execute_command(cmd, context=None):
    """Execute a system command and return the output.
    Example:
    { "execute_command": { "cmd": "ls -la" } }
    """
    if 'current_dir' in context.data:
        cmd = f'cd {context.data["current_dir"]} && {cmd}'
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        error = result.stderr.decode('utf-8')
        if error:
            return f"Error: {error}"
        return output
    except subprocess.CalledProcessError as e:
        return f"Command '{cmd}' failed with error: {e}"

@command()
async def mkdir(directory, context=None):
    """Create a new directory.
    Example:
    { "mkdir": { "directory": "new_folder" } }
    """
    if 'current_dir' in context.data:
        directory = os.path.join(context.data['current_dir'], directory)
    try:
        os.makedirs(directory, exist_ok=True)
        return f"Directory '{directory}' created successfully."
    except Exception as e:
        return f"Failed to create directory '{directory}': {e}"

@command()
async def tree(directory='', context=None):
    """List directory structure excluding patterns from .gitignore.
    Example:
    { "tree": { "directory": "" } }
    """
    if 'current_dir' in context.data:
        directory = os.path.join(context.data['current_dir'], directory)
    gitignore_path = os.path.join(directory, '.gitignore')
    exclude_patterns = parse_gitignore(gitignore_path)

    def is_excluded(path):
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def list_dir(dir_path):
        tree_structure = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
            files = [f for f in files if not is_excluded(os.path.join(root, f))]
            tree_structure.append((root, dirs, files))
        return tree_structure

    tree_structure = list_dir(directory)
    return tree_structure


def parse_gitignore(gitignore_path):
    if not os.path.exists(gitignore_path):
        return []
    with open(gitignore_path, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return patterns
