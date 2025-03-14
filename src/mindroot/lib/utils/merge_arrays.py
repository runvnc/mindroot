import json
import re
from itertools import chain
from partial_json_parser import loads as partial_json_loads

test="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}}][{"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}}][{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}}][{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

test2="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}}], [{"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}}][{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}}][{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

test3="""
[{"think": {"extensive_chain_of_thoughts": "Let me review each route file for missing imports:\n\n1. upload_routes.py:\n- Needs traceback for error handling\n\n2. processing_routes.py:\n- Needs datetime for timestamp handling\n- Needs to import load_financial_assumptions\n\n3. results_routes.py:\n- Needs datetime for current_datetime usage\n\n4. common.py looks complete\n\nLet me update these files one at a time with the missing imports."}}], [{"write": {"fname": "/xfiles/maverickcre/plugins/cre_b"}}]
"""

test4="""
[{"reasoning": "Analysis..."}] <<CUT_HERE>>[{"say": {"text": "Hello"}}]

[{"json_encoded_md": {"markdown": "content..."}}]
"""

def merge_json_arrays(data, partial=False):
    """Merge multiple JSON arrays into a single array.
    
    This function detects patterns like '[{...}][{...}]' or '[{...}], [{...}]'
    and combines them into a single valid array '[{...}, {...}]'
    
    Args:
        data (str): The string containing one or more JSON arrays
        partial (bool): If True, use partial_json_loads to handle incomplete JSON
    
    Returns:
        list: A merged list of all commands found in the input arrays
    """
    # If the input is empty or null, return empty list
    if not data or data.strip() == '':
        return []
    
    # Try first with regular JSON parsing in case it's already valid
    try:
        # For a single valid JSON array, just return it directly
        if partial:
            load_json = partial_json_loads
        else:
            load_json = json.loads
        
        # Check if it's already a valid JSON array
        result = load_json(data)
        if isinstance(result, list):
            return result
    except Exception:
        pass  # If it fails, continue with merging approach
    
    # Detect and handle <<CUT_HERE>> markers that might separate JSON arrays
    if "<<CUT_HERE>>" in data:
        parts = data.split("<<CUT_HERE>>")
        all_commands = []
        for part in parts:
            if part.strip():
                try:
                    commands = merge_json_arrays(part.strip(), partial)
                    if isinstance(commands, list):
                        all_commands.extend(commands)
                except Exception:
                    pass
        return all_commands

    # Process the data to find and merge multiple arrays
    data = data.strip()
    
    # Split on patterns that likely indicate separate arrays
    # This handles cases like: [...]   [...] or [...]\n[...]
    parts = re.split(r"\]\s*,*\s*\[", data)
    
    if len(parts) == 1 and parts[0] == data:
        # If no standard array boundaries found, try other patterns
        parts = re.split(r"\]\s*\n+\s*\[", data)  # Handle arrays separated by newlines
    
    if len(parts) == 1 and parts[0] == data:
        # Try to catch reasoning/think blocks that often appear separately
        reasoning_pattern = r"\]\s*(?:<+CUT_HERE>+)\s*\["
        parts = re.split(reasoning_pattern, data)
    
    # Process each part to form valid JSON arrays
    arrays = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:  # Skip empty parts
            continue
            
        # Fix beginning of part
        if i > 0:  # Not the first part needs a leading [
            if not part.startswith("{") and not part.startswith("["):
                part = "[" + part
            elif part.startswith("{"):  # Part starts with object, needs array wrapper
                part = "[" + part
        elif not part.startswith("["):  # First part should start with [
            part = "[" + part
            
        # Fix end of part
        if i < len(parts) - 1:  # Not the last part needs a closing ]
            if not part.endswith("]"):  # Make sure it ends with ]
                part = part + "]"
        elif not part.endswith("]"):  # Last part should end with ]
            part = part + "]"
            
        # Remove trailing commas
        if part.endswith(",]"):
            part = part[:-2] + "]"
            
        try:
            # Try to parse this part
            if partial:
                parsed = partial_json_loads(part)
            else:
                parsed = json.loads(part)
                
            if isinstance(parsed, list):
                arrays.append(parsed)
            else:
                # If we got a non-list (shouldn't happen), wrap it
                arrays.append([parsed])
        except Exception as e:
            if partial:
                # For partial mode, we might need to handle more cases
                try:
                    # Try fixing newlines
                    part = part.replace("\n", "\\n")
                    # Remove trailing escaped newlines
                    if part.endswith("\\n"):
                        part = part[:-2]
                    parsed = partial_json_loads(part)
                    if isinstance(parsed, list):
                        arrays.append(parsed)
                    else:
                        arrays.append([parsed])
                except Exception:
                    # If still failing, just skip this part
                    pass
    
    # Combine all parsed arrays into a single list
    if arrays:
        return list(chain.from_iterable(arrays))
    
    # If all else fails, try the original json.loads as fallback
    # This preserves the original behavior if nothing else works
    if partial:
        return partial_json_loads(data)
    return json.loads(data)

# Uncomment to test:
# ret = merge_json_arrays(test4, False)
# print("successful parsing")
# for item in ret:
#     print('-----------------------------------')
#     print(item)
#     print('-----------------------------------')
