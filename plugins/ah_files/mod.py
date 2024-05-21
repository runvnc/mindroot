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
    """Replace text between two strings in a file."""
    if 'current_dir ' in context.data:
        fname = context.data['current_dir'] + '/' + fname
    with open(fname, 'r') as f:
        lines = f.readlines()
    with open(fname, 'w') as f:
        for line in lines:
            if start in line:
                f.write(line)
                f.write(text)
            elif end in line:
                f.write(line)
                break
            else:
                f.write(line)
        print(f'Replaced text between {start} and {end} in {fname}')

