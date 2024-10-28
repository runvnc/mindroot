def escape_for_json(s: str) -> str:
    """
    Escape a string to make it safe for use as a JSON property value.
    
    Args:
        s (str): The input string to escape
        
    Returns:
        str: The escaped string safe for JSON
        
    Examples:
        >>> escape_for_json('Hello "world"')
        'Hello \\"world\\"'
        >>> escape_for_json('Line 1\nLine 2')
        'Line 1\\nLine 2'
    """
    # Define escapes for control characters
    escapes = {
        '\\': '\\\\',
        '"': '\\"',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\b': '\\b',
        '\f': '\\f'
    }
    
    # Process each character and escape as needed
    result = ''
    for char in s:
        result += escapes.get(char, char)
        
    return result
