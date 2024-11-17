import re
import json

def escape_markdown_code_blocks(text):
    """
    Escape newlines within markdown code blocks (text between triple backticks)
    to make them JSON-safe while preserving regular markdown newlines.
    
    Args:
        text (str): Input text containing markdown code blocks
        
    Returns:
        str: Text with newlines escaped only within code blocks
    """
    try:
        # Replace newlines in code blocks with escaped version
        processed = re.sub(r'```[\s\S]*?```',
                          lambda m: m.group(0).replace('\n', '\\n'),
                          text)
        return processed
    except Exception as e:
        raise Exception(f"Error processing markdown code blocks: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Test markdown with multiple code blocks
    test_markdown = '''# Example Markdown

Here's some Python code:

```python
def hello():
    print('world')
    return 42
```

And here's some JSON:

```json
{
    "name": "test",
    "value": 123
}
```

And a block with no language specified:

```
plain text
with multiple
lines
```
'''

    print("Original Markdown:")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    # Process the markdown
    processed = escape_markdown_code_blocks(test_markdown)
    
    # Create JSON object
    json_obj = {"markdown": processed}
    
    print("\nAs JSON:")
    print("-" * 60)
    print(json.dumps(json_obj, indent=2))
    print("-" * 60)
    
    # Verify roundtrip
    try:
        parsed = json.loads(json.dumps(json_obj))
        print("\nVerification: Successfully parsed as valid JSON!")
        print("\nParsed content (notice proper newlines in code blocks):")
        print("-" * 60)
        print(parsed['markdown'])
        print("-" * 60)
    except json.JSONDecodeError as e:
        print(f"\nError: JSON validation failed: {e}")
