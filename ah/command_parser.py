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
    remaining_buffer = buffer
    
    # Find the outermost square brackets
    start = buffer.find('[')
    end = buffer.rfind(']')
    
    if start == -1 or end == -1 or start > end:
        return [], buffer
    
    # Extract the content within the outermost square brackets
    content = buffer[start+1:end].strip()
    
    # Split the content into individual command strings
    command_strings = []
    bracket_count = 0
    current_command = ""
    
    for char in content:
        if char == '{':
            bracket_count += 1
        elif char == '}':
            bracket_count -= 1
        
        current_command += char
        
        if bracket_count == 0 and char == '}':
            command_strings.append(current_command.strip())
            current_command = ""
    
    # Parse each command string
    for cmd_str in command_strings:
        try:
            cmd = json.loads('{' + cmd_str + '}')
            if isinstance(cmd, dict) and len(cmd) == 1:
                cmd_name = next(iter(cmd))
                cmd_args = cmd[cmd_name]
                if isinstance(cmd_args, dict) and len(cmd_args) > 0:
                    complete_commands.append(cmd)
        except json.JSONDecodeError:
            pass
    
    # Update the remaining buffer
    if complete_commands:
        remaining_buffer = buffer[end+1:].strip()
    
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

if __name__ == '__main__':
    unittest.main()
