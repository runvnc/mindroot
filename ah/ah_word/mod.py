from ..commands import command
from .msword import replace_all

@command()
async def word_replace_all(file_path, replacements, save_path=None, context=None):
    """Replace all occurrences of specified strings in a Word document.

    Parameters:

    file_path (str): The path to the input Word document.
    replacements (dict): A dictionary where keys are strings to be replaced, and values are their replacements.

    save_path (str, optional): The path to save the modified document. If not provided, the original file will be overwritten.


    Example:

    [
    { "word_replace_all": { 
        "file_path": "/path/to/document.docx", 
        "replacements": {
            "old text": "new text",
            "another old": "another new"
        },
        "save_path": "/path/to/output.docx"
    } }
    ]

    """

    try:
        result = replace_all(file_path, replacements, save_path, context)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

