import json
import re
from typing import List, Dict, Tuple, Any
from partial_json_parser import loads, ensure_json
from lib.json_str_block import replace_raw_blocks
from lib.utils.parse_json_newlines_partial import json_loads
from lib.utils.merge_arrays import merge_json_arrays
from lib.json_escape import escape_for_json
import sys
import traceback

# TODO: clean up, just use normal tool calling (never lol),
# or maybe we can use this code as the kernel of a niche horror
# film targeted at engineers

def parse_streaming_commands(buffer: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parse streaming commands from a buffer, identifying complete commands.
    
    Args:
    buffer (str): The current buffer of streamed data.
    
    Returns:
    Tuple[List[Dict[str, Any]], str]: A tuple containing a list of complete commands and the last partial command (if any).
    """
    complete_commands = []
    current_partial = None

    if "<<CUT_HERE>>" in buffer:
        buffer = buffer[buffer.find("<<CUT_HERE>>")+12:] + ' '

    if not buffer.strip():
        return [], None
   
    try:
        raw_replaced = replace_raw_blocks(buffer)
        #raw_replaced = escape_for_json(raw_replaced)
        complete_commands = json.loads(raw_replaced)
        #print(1)
        return complete_commands, None
    except Exception:
        try:
            #print("Trying merge_json_arrays in parse_streaming_commands")
            complete_commands = merge_json_arrays(raw_replaced)
            if len(complete_commands) > 0:
                return complete_commands, None
        except Exception:
            pass
            
        try:
            raw_replaced = escape_for_json(buffer)
            complete_commands = json.loads(raw_replaced)
            ##print("Found complete command from escape_for_json")
            #print(2)
            return complete_commands, None
        except Exception:
            pass
        try:
            ##print("trying merge_json_arrays with partial=True")
            complete_commands = merge_json_arrays(buffer, partial=True)
            num_commands = len(complete_commands)
            #print("complete_commands before assigning current partial:", complete_commands)
            #print("current_partial", current_partial)
 
            if num_commands > 1:
                complete_commands = complete_commands[:num_commands-1]
                current_partial = complete_commands[-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            #print("complete_commands AFTER assigning current partial:", complete_commands)
            #print("current_partial", current_partial)

            ##print("Found partial command from merge_json_arrays")
            #print(3)
            return complete_commands, current_partial
        except Exception as e:
            ##print("Failed to find partial command from merge_json_arrays")
            ##print(e)
            #traceback.#print_exc()
            pass

        try:
            raw_replaced = replace_raw_blocks(buffer)
            complete_commands = loads(raw_replaced)
            num_commands = len(complete_commands)
            #print("parsed, num complete commands:", num_commands)
            if num_commands > 1:
                current_partial = complete_commands[-1]
                complete_commands = complete_commands[:num_commands-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            #print(4)
            return complete_commands, current_partial
        except Exception as e:
            #print("Failed to parse using loads")
            #print(e)
            #print("raw_replaced:", raw_replaced)
            #print("buffer:", buffer)
            pass

        try:
            complete_commands = json.loads(buffer)
            num_commands = len(complete_commands)
            #print(4.5)

            #print("parsed, num complete commands:", num_commands)
            if len(complete_commands) > 0:
                return complete_commands, None
 
            return complete_commands, current_partial
        except Exception as e:
            #print("Failed to parse using loads")
            #print(e)
            #print("buffer:", buffer)
            pass

        try:
            complete_commands = merge_json_arrays(raw_replaced, partial=True)
            num_commands = len(complete_commands)
            if num_commands > 1:
                complete_commands = complete_commands[:num_commands-1]
                current_partial = complete_commands[-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            ##print("complete_commands before assigning current partial:", complete_commands)
            ##print("Found partial command from merge_json_arrays")
            #print(5)
            return complete_commands, current_partial
        except Exception as e:
            ##print("Failed to find partial command from merge_json_arrays")
            ##print(e)
            #traceback.#print_exc()
            pass


        try:
            complete_commands = json_loads(raw_replaced)
            num_commands = len(complete_commands)
            if num_commands > 1:
                complete_commands = complete_commands[:num_commands-1]
                current_partial = complete_commands[-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            #print(6)
            return complete_commands, current_partial
        except Exception:
            pass
        try:
            complete_commands = json_loads(buffer)
            num_commands = len(complete_commands)
            if num_commands > 1:
                current_partial = complete_commands[-1]
                complete_commands = complete_commands[:num_commands-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            #print(7)
            return complete_commands, current_partial
        except Exception:
            # if ends in ']', then may be end of command list
            #if it failed to parse, write buffer that failed to debug in orange text
            if buffer[-1] == ']':
                # try one more thing: there might be an extra } before the ]
                buffer = buffer[:-2] + "]"
                try:
                    complete_commands = json_loads(buffer)
                    num_commands = len(complete_commands)
                    if num_commands > 1:
                        current_partial = complete_commands[-1]
                        complete_commands = complete_commands[:num_commands-1]
                    else:
                        current_partial = complete_commands[-1]
                        complete_commands = []
                    #print(7)
                    return complete_commands, current_partial
                except Exception:
                    #print("\033[93m", end="")
                    #print(f"Failed to parse buffer even with escaping: {buffer}")
                    #print("\033[0m", end="")
                    pass
        try:
            raw_replaced = escape_for_json(buffer)
            parsed_data = loads(raw_replaced)
            num_commands = len(parsed_data)
            if num_commands > 1:
                complete_commands = parsed_data[:num_commands-1]
            else:
                complete_commands = []
            current_partial = parsed_data[-1]
            return complete_commands, current_partial
        except Exception:
            pass

        try:
            complete_commands = json.loads(buffer + "]")
            num_commands = len(complete_commands)
            return complete_commands, None
        except Exception:
            # If parsing fails, return an empty list of commands and None as partial
            #print(9)
            return [], None
                  
        try:
            parsed_data = loads(raw_replaced)
            num_commands = len(parsed_data)
            if num_commands > 1:
                complete_commands = parsed_data[:num_commands-1]
            else:
                complete_commands = []
            current_partial = parsed_data[-1]
            return complete_commands, current_partial
        except Exception:
            # If parsing fails, return an empty list of commands and None as partial
            #print(9)
            return [], None
    if not isinstance(current_partial, dict):
        current_partial = None
    #print(10)
    return complete_commands, current_partial

def invalid_start_format(str):
    # string is supposed to be an array in JSON format
    # if it starts with a non-whitespace character that is not [
    # then it is invalid and we return true
    # we might want to use a regex
    # try to match anything that is not a whitespace character or [
    # if it matches, then it is invalid and return True
    is_invalid = re.match(r'^[^\s\[\{]', str)
    return is_invalid


# Test cases
import unittest

class TestCommandParser(unittest.TestCase):
    def test_single_complete_command(self):
        buffer = '[{"say": {"text": "Hello", "done": true}}]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"say": {"text": "Hello", "done": True}})
        self.assertIsNone(partial)
    
    def test_multiple_complete_commands(self):
        buffer = '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "value1"}}]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0], {"say": {"text": "Hello"}})
        self.assertEqual(commands[1], {"do_something": {"arg1": "value1"}})
        self.assertIsNone(partial)
    
    def test_partial_command(self):
        buffer = '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "valu'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"say": {"text": "Hello"}})
        self.assertEqual(partial, {"do_something": {"arg1": "valu"}})
    
    def test_empty_buffer(self):
        buffer = ''
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertIsNone(partial)
    
    def test_invalid_json(self):
        buffer = '[{"say": {"text": "Hello"}, {"invalid": "command"}]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertIsNone(partial)
    
    def test_nested_objects(self):
        buffer = '[{"complex_command": {"nested": {"key": "value"}}}]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"complex_command": {"nested": {"key": "value"}}})
        self.assertIsNone(partial)
    
    def test_partial_nested_objects(self):
        buffer = '[ {"complex_command": {"nested": {"key": "val'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {"complex_command": {"nested": {"key": "val"}}})

    def test_partial_think_command(self):
        buffer = '[{ "think": {'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {"think": {} })

    def test_partial_think_command_with_thoughts(self):
        buffer = '[{ "think": { "thoughts": {'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {"think": {"thoughts": {} }})

    def test_partial_think_command_with_complete_thoughts(self):
        buffer = '[{ "think": { "thoughts": "I am thinking" } }]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"think": {"thoughts": "I am thinking"}})
        self.assertIsNone(partial)

    def test_malformed_json(self):
        buffer = '[{"key": "value"'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {"key": "value"})



def ex6():
    buffer = """
[ {"write": { "filename": "/test.py",
              "text": "START_RAW
def foo():
    #print('hello world')
END_RAW
" }
 } 
]
"""
    commands, partial = parse_streaming_commands(buffer)
    #print(commands)
    #print(partial)


