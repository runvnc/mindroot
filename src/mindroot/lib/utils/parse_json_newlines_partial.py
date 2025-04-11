import json
import sys
import partial_json_parser

def json_loads(content: str):
    """Parse a partial or complete JSON string with preprocessing for newlines and control characters."""
    proessed_content = content
    try:
        lines = [line.strip() for line in content.split('\n')]
        processed_content = '\\n'.join(lines)

        # check for extra "\\n" at end
        if processed_content.endswith("\\n"):
            processed_content = processed_content[:-2]

        try:
            parsed = json.loads(processed_content)
        except Exception as e:
            parsed = partial_json_parser.loads(processed_content)
        
        return parsed
            
    except Exception as e:
        print(f"Error in json_loads: {e}.\nContent: {content}\nProcessed Content: {proessed_content}.\n")
        return None

