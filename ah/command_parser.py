import json
from typing import List, Dict, Tuple, Any

def parse_streaming_commands(buffer: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parse streaming commands from a buffer, identifying complete commands.
    
    Args:
    buffer (str): The current buffer of streamed data.
    
    Returns:
    Tuple[List[Dict[str, Any]], str]: A tuple containing a list of complete commands and the remaining buffer.
    """
    complete_commands = []
    remaining_buffer = buffer.strip()
    
    # Find the outermost square brackets
    start = remaining_buffer.find('[')
    end = remaining_buffer.rfind(']')
    
    if start == -1:
        # If no opening bracket, treat the whole buffer as a potential command
        content = remaining_buffer
    elif end == -1 or start > end:
        # If no closing bracket or mismatched brackets, return no commands
        return [], remaining_buffer
    else:
        # Extract the content within the outermost square brackets
        content = remaining_buffer[start+1:end].strip()
        remaining_buffer = remaining_buffer[end+1:].strip()
    
    # Split the content into individual command strings
    bracket_count = 0
    current_command = ""
    in_string = False
    escape_next = False
    
    for char in content:
        if not in_string:
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
        
        if char == '"' and not escape_next:
            in_string = not in_string
        
        escape_next = char == '\\' and not escape_next
        
        current_command += char
        
        if bracket_count == 0 and char == '}':
            try:
                cmd = json.loads(current_command)
                if isinstance(cmd, dict) and len(cmd) == 1:
                    cmd_name = next(iter(cmd))
                    cmd_args = cmd[cmd_name]
                    if isinstance(cmd_args, dict):
                        complete_commands.append(cmd)
            except json.JSONDecodeError:
                pass
            current_command = ""
    
    # If there's an incomplete command at the end, add it back to the remaining buffer
    if current_command.strip():
        remaining_buffer = current_command + remaining_buffer
    
    # Handle cases where there are no square brackets
    if not complete_commands and remaining_buffer:
        try:
            cmd = json.loads(remaining_buffer)
            if isinstance(cmd, dict) and len(cmd) == 1:
                cmd_name = next(iter(cmd))
                cmd_args = cmd[cmd_name]
                if isinstance(cmd_args, dict):
                    complete_commands.append(cmd)
                    remaining_buffer = ""
        except json.JSONDecodeError:
            pass
    
    return complete_commands, remaining_buffer

# Test cases
import unittest

class TestCommandParser(unittest.TestCase):
    
    def test_single_complete_command(self):
        buffer = '[{"say": {"text": "Hello", "done": true}}]'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"say": {"text": "Hello", "done": True}})
        self.assertEqual(remaining, '')
    
    def test_multiple_complete_commands(self):
        buffer = '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "value1"}}]'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0], {"say": {"text": "Hello"}})
        self.assertEqual(commands[1], {"do_something": {"arg1": "value1"}})
        self.assertEqual(remaining, '')
    
    def test_partial_command(self):
        buffer = '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "valu'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"say": {"text": "Hello"}})
        self.assertEqual(remaining, '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "valu')
    
    def test_empty_buffer(self):
        buffer = ''
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(remaining, '')
    
    def test_invalid_json(self):
        buffer = '[{"say": {"text": "Hello"}, {"invalid": "command"}]'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"say": {"text": "Hello"}})
        self.assertEqual(remaining, '[{"say": {"text": "Hello"}, {"invalid": "command"}]')
    
    def test_nested_objects(self):
        buffer = '[{"complex_command": {"nested": {"key": "value"}}}]'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"complex_command": {"nested": {"key": "value"}}})
        self.assertEqual(remaining, '')
    
    def test_partial_nested_objects(self):
        buffer = '[{"complex_command": {"nested": {"key": "val'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(remaining, '[{"complex_command": {"nested": {"key": "val')

    def test_partial_think_command(self):
        buffer = '{ "think": '
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(remaining, '{ "think": ')

    def test_partial_think_command_with_thoughts(self):
        buffer = '{ "think": { "thoughts": '
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(remaining, '{ "think": { "thoughts": ')

    def test_partial_think_command_with_complete_thoughts(self):
        buffer = '[{ "think": { "thoughts": "I am thinking" } }'
        commands, remaining = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {"think": {"thoughts": "I am thinking"}})
        self.assertEqual(remaining, '')

if __name__ == '__main__':
    unittest.main()
