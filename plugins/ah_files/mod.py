from ..services import service
from ../commands import command

@command()
def write(fname, text, context=None):
    """Write text to a file. Will overwrite the file if it exists."""
    if 'current_dir ' in context.data:
        fname = context.data['current_dir'] + '/' + fname
    with open(fname, 'w') as f:
        f.write(text)
        print(f'Wrote text to {fname}')

@command()
def read(fname, context=None):
    """Read text from a file."""
    if 'current_dir ' in context.data:
        fname = context.data['current_dir'] + '/' + fname
    with open(fname, 'r') as f:
        text = f.read()
        print(f'Read text from {fname}: {text}')
        return text

@command()
def replace_between_inclusive(fname, start, end, text, context=None):
    """Replace text between two strings in a file, including the start and end strings."""
    if 'current_dir ' in context.data:
        fname = context.data['current_dir'] + '/' + fname
    with open(fname, 'r') as f:
        content = f.read()
    start_index = content.find(start)
    end_index = content.find(end, start_index)
    if start_index != -1 and end_index != -1:
        end_index += len(end)  # Include the end string in the replacement
        new_content = content[:start_index] + start + text + end + content[end_index:]
        with open(fname, 'w') as f:
            f.write(new_content)
        print(f'Replaced text between {start} and {end} in {fname}')
    else:
        print(f'Could not find the start or end text in {fname}')

