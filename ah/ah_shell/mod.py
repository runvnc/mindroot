import os
import subprocess
import fnmatch
from ..commands import command
from gitignore_parser import parse_gitignore
from collections import OrderedDict

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
    matches = parse_gitignore(gitignore_path)

    def exclude(path):
        ignore = [ '.git', 'node_modules', 'dist', 'build', 'coverage', '__pycache__' ]
        if path.startswith('.'):
            return True
        if any(fnmatch.fnmatch(path, pattern) for pattern in ignore):
            return True
        return matches(path)

    def list_dir(dir_path):
        tree_structure = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if not matches(os.path.join(root, d))]
            files = [f for f in files if not matches(os.path.join(root, f))]
            node = OrderedDict()
            node['root'] = root
            node['dirs'] = dirs
            node['files'] = files
            tree_structure.append(node)

        return tree_structure

    tree_structure = list_dir(directory)
    return tree_structure


class TestContext:
    def __init__(self, data):
        self.data = data

if __name__ == '__main__':
    import asyncio
    from pprint import pprint
    async def main():
        cmd = 'ls -la'
        context = TestContext({'current_dir': '/files/ah'})

        result = await execute_command(cmd, context=context)
        print(result)
        directory = 'new_folder'
        result = await mkdir(directory, context=context)
        print(result)
        directory = ''
        result = await tree(directory, context=context)
        pprint(result)
    asyncio.run(main())
