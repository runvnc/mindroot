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
    if '<<CUT_HERE>>' in buffer:
        buffer = buffer[buffer.find('<<CUT_HERE>>') + 12:] + ' '
    if not buffer.strip():
        return ([], None)
    try:
        raw_replaced = replace_raw_blocks(buffer)
        complete_commands = json.loads(raw_replaced)
        return (complete_commands, None)
    except Exception:
        try:
            complete_commands = merge_json_arrays(raw_replaced)
            if len(complete_commands) > 0:
                return (complete_commands, None)
        except Exception:
            pass
        try:
            raw_replaced = escape_for_json(buffer)
            complete_commands = json.loads(raw_replaced)
            return (complete_commands, None)
        except Exception:
            pass
        try:
            d = 1
        except Exception as e:
            pass
        try:
            raw_replaced = replace_raw_blocks(buffer)
            complete_commands = loads(raw_replaced)
            num_commands = len(complete_commands)
            if num_commands > 1:
                current_partial = complete_commands[-1]
                complete_commands = complete_commands[:num_commands - 1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            return (complete_commands, current_partial)
        except Exception as e:
            pass
        try:
            complete_commands = json.loads(buffer)
            num_commands = len(complete_commands)
            if len(complete_commands) > 0:
                return (complete_commands, None)
            return (complete_commands, current_partial)
        except Exception as e:
            pass
        try:
            complete_commands = merge_json_arrays(raw_replaced, partial=True)
            num_commands = len(complete_commands)
            if num_commands > 1:
                complete_commands = complete_commands[:num_commands - 1]
                current_partial = complete_commands[-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            return (complete_commands, current_partial)
        except Exception as e:
            pass
        try:
            complete_commands = json_loads(raw_replaced)
            num_commands = len(complete_commands)
            if num_commands > 1:
                complete_commands = complete_commands[:num_commands - 1]
                current_partial = complete_commands[-1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            return (complete_commands, current_partial)
        except Exception:
            pass
        try:
            complete_commands = json_loads(buffer)
            num_commands = len(complete_commands)
            if num_commands > 1:
                current_partial = complete_commands[-1]
                complete_commands = complete_commands[:num_commands - 1]
            else:
                current_partial = complete_commands[-1]
                complete_commands = []
            return (complete_commands, current_partial)
        except Exception:
            if buffer[-1] == ']':
                buffer = buffer[:-2] + ']'
                try:
                    complete_commands = json_loads(buffer)
                    num_commands = len(complete_commands)
                    if num_commands > 1:
                        current_partial = complete_commands[-1]
                        complete_commands = complete_commands[:num_commands - 1]
                    else:
                        current_partial = complete_commands[-1]
                        complete_commands = []
                    return (complete_commands, current_partial)
                except Exception:
                    pass
        try:
            raw_replaced = escape_for_json(buffer)
            parsed_data = loads(raw_replaced)
            num_commands = len(parsed_data)
            if num_commands > 1:
                complete_commands = parsed_data[:num_commands - 1]
            else:
                complete_commands = []
            current_partial = parsed_data[-1]
            return (complete_commands, current_partial)
        except Exception:
            pass
        try:
            complete_commands = json.loads(buffer + ']')
            num_commands = len(complete_commands)
            return (complete_commands, None)
        except Exception:
            return ([], None)
        try:
            parsed_data = loads(raw_replaced)
            num_commands = len(parsed_data)
            if num_commands > 1:
                complete_commands = parsed_data[:num_commands - 1]
            else:
                complete_commands = []
            current_partial = parsed_data[-1]
            return (complete_commands, current_partial)
        except Exception:
            return ([], None)
    if not isinstance(current_partial, dict):
        current_partial = None
    return (complete_commands, current_partial)

def invalid_start_format(str):
    is_invalid = re.match('^[^\\s\\[\\{]', str)
    return is_invalid
import unittest

class TestCommandParser(unittest.TestCase):

    def test_single_complete_command(self):
        buffer = '[{"say": {"text": "Hello", "done": true}}]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {'say': {'text': 'Hello', 'done': True}})
        self.assertIsNone(partial)

    def test_multiple_complete_commands(self):
        buffer = '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "value1"}}]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0], {'say': {'text': 'Hello'}})
        self.assertEqual(commands[1], {'do_something': {'arg1': 'value1'}})
        self.assertIsNone(partial)

    def test_partial_command(self):
        buffer = '[{"say": {"text": "Hello"}}, {"do_something": {"arg1": "valu'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {'say': {'text': 'Hello'}})
        self.assertEqual(partial, {'do_something': {'arg1': 'valu'}})

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
        self.assertEqual(commands[0], {'complex_command': {'nested': {'key': 'value'}}})
        self.assertIsNone(partial)

    def test_partial_nested_objects(self):
        buffer = '[ {"complex_command": {"nested": {"key": "val'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {'complex_command': {'nested': {'key': 'val'}}})

    def test_partial_think_command(self):
        buffer = '[{ "think": {'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {'think': {}})

    def test_partial_think_command_with_thoughts(self):
        buffer = '[{ "think": { "thoughts": {'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {'think': {'thoughts': {}}})

    def test_partial_think_command_with_complete_thoughts(self):
        buffer = '[{ "think": { "thoughts": "I am thinking" } }]'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], {'think': {'thoughts': 'I am thinking'}})
        self.assertIsNone(partial)

    def test_malformed_json(self):
        buffer = '[{"key": "value"'
        commands, partial = parse_streaming_commands(buffer)
        self.assertEqual(len(commands), 0)
        self.assertEqual(partial, {'key': 'value'})

def ex6():
    buffer = '\n[ {"write": { "filename": "/test.py",\n              "text": "START_RAW\ndef foo():\n    #print(\'hello world\')\nEND_RAW\n" }\n } \n]\n'
    commands, partial = parse_streaming_commands(buffer)