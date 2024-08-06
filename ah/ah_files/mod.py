from .backup_file import backup_file
from ..commands import command
import os
from .backup_file import restore_file
import glob

@command()
async def write(fname="", text="", context=None):
    """Write text to a file. Will overwrite the file if it exists.
    Make sure you know the full path first.
    Note: Do NOT use placeholders instead of full source, such as " # ..keep existing code"
          as this will not work and will effectively delete all of that code that was there before.
        All text must be provided to be written to the file.

    Example:
    { "write": { "fname": "/path/to/file1.txt", "text": "This is the text to write to the file." } }

    """
    print("Write file, context is:", context, 'context.data is:', context.data)
    if 'current_dir' in context.data:
        if fname.startswith('/') or fname.startswith('./') or fname.startswith('../'):
            fname = fname + ''
        else:
            if 'current_dir' in context.data:
                fname = context.data['current_dir'] + '/' + fname
    
    dirname = os.path.dirname(fname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if os.path.isfile(fname):
        backup_file(fname)
    with open(fname, 'w') as f:
        f.write(text)
        print(f'Wrote text to {fname}')
    return True


@command()
async def read(fname="", context=None):
    """Read text from a file.
    You should know the full path.
    Example:
    { "read": { "fname": "/path/to/file1.txt" } }
    """
    if 'current_dir' in context.data:
        if fname.startswith('/') or fname.startswith('./') or fname.startswith('../'):
            fname = fname + ''
        else:
            if 'current_dir' in context.data:
                fname = context.data['current_dir'] + '/' + fname
    else:
        print('No current_dir in context.data')
        print('context.data=', context.data)

    print('context=', context, 'fname=', fname)
    print('context.data = ', context.data)
    with open(fname, 'r') as f:
        text = f.read()
        print(f'Read text from {fname}: {text}')
        return text

@command()
async def replace_inclusive(fname=None, starts_with=None, ends_with=None, text=None, context=None):
    """Replace text between two strings in a file including start and end strings.

    Parameters:

    fname - The file to replace text in.
    starts_with - The JSON-encoded/safe start string.
    ends_with - The JSON-encoded/safe end string.
    text - The JSON-encoded/safe text to replace existing content with, including start and end strings.

    Important: remember that since this is JSON, strings must be properly escaped, such as double quotes, etc.

    Example:

    { "replace_inclusive": { "fname": "/path/to/somefile.ext", "starts_with": "start of it",
      "ends_with": "end of it", "text": "start of it\\nnew text\\nend of it" } }


    Example:
    
    { "replace_inclusive": { "fname": "example.py", "starts_with": "def hello():\\n", 
      "ends_with": "\\n    return 'hi'", "text": "def hello():\\n    print('hi in console')\\n    return 'hello'"}}

    """
    if 'current_dir' in context.data:
        if fname.startswith('/') or fname.startswith('./') or fname.startswith('../'):
            fname = fname + ''
        else:
            if 'current_dir' in context.data:
                fname = context.data['current_dir'] + '/' + fname
 
    backup_file(fname)
    with open(fname, 'r') as f:
        content = f.read()
    print(f"read from file at {fname}")
    print("file contents:")
    print(content)
    start_index = content.find(starts_with)
    end_index = content.find(ends_with, start_index)
    if start_index != -1 and end_index != -1:
        end_index += len(ends_with)
        new_content = content[:start_index] + text + content[end_index:]
        with open(fname, 'w') as f:
            f.write(new_content)
        print(f'Replaced text between {starts_with} and {ends_with} in {fname}')
    else:
        if start_index == -1:
            raise Exception("Could not find starts_with")
        if end_index == -1:
            raise Exception("Could not find ends_with")

    return True

@command()
async def dir(directory='', context=None):
    """List files in directory.
    Parameter: directory - The directory to list files in. If empty, lists files in the current directory.

    Example:
    
    { "dir": "/path/to/subdir1" }

    Other Example (current dir)

    { "dir": "" }

    """
    if directory.startswith('/') or directory.startswith('./') or directory.startswith('../'):
        directory = directory + ''
    else:
        if 'current_dir' in context.data:
            directory = context.data['current_dir'] + '/' + directory
    files = os.listdir(directory)
    print(f'Files in {directory}: {files}')
    return files

@command()
async def restore(fname, timestamp=None, context=None):
    """Restore a file from its backup. If no timestamp is specified, restore the latest backup.
    Parameters:

    fname - The file to restore.
    timestamp - The specific timestamp of the backup to restore. If omitted, the latest backup will be used.

    Example:

    { "restore": { "fname": "file1.txt", "timestamp": "12_24_11_00_00" } }

    Example (latest backup):

    { "restore": { "fname": "file1.txt" } }

    """
    if 'current_dir' in context.data:
        fname = context.data['current_dir'] + '/' + fname
    restore_file(fname, timestamp)
    print(f'Restored {fname} from backup.')


@command()
async def show_backups(context=None):
    """List all backup files in the .backup directory.
    Example:
    { "show_backups": {} }
    """
    backup_dir = '.backup'
    if not os.path.exists(backup_dir):
        print(f"The backup directory {backup_dir} does not exist.")
        return []
    backups = glob.glob(os.path.join(backup_dir, '*'))
    backup_files = [os.path.basename(backup) for backup in backups]
    print(f"Backup files: {backup_files}")
    return backup_files

@command()
async def cd(directory, context=None):
    """Change the current working directory.

    Parameter: directory - The directory to change to. This can be a relative or absolute path.
                           If unsure, use absolute path.

    Example:

    { "cd": "subdir1" }

    Other Example (parent dir)

    { "cd": ".." }

    """
    if 'current_dir' not in context.data:
        context.data['current_dir'] = os.getcwd()
    if directory.startswith('/'):
        new_dir = directory
    else:
        new_dir = os.path.realpath(os.path.join(context.data['current_dir'], directory))
    if os.path.isdir(new_dir):
        context.data['current_dir'] = new_dir
        context.save_context()
        print(f'Changed current directory to {new_dir}')
    else:
        print(f'Directory {new_dir} does not exist.')
    return True
