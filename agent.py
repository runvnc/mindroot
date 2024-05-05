import json
from ollama import stream_chat

def parse_cmd_stream(stream, cmd_callback=None):
    buffer = ""
    stack = []
    in_string = False
    escape_next = False

    for chunk in stream:
        buffer += chunk
        for char in chunk:
            if char == '"' and not escape_next:
                in_string = not in_string
            elif char == '\\' and in_string:
                escape_next = True
            elif char == '{' and not in_string:
                stack.append(char)
            elif char == '}' and not in_string:
                if stack and stack[-1] == '{':
                    stack.pop()
                    if not stack:
                        # Found a complete command object
                        try:
                            cmd_obj = json.loads(buffer)
                            cmd_name = next(iter(cmd_obj))
                            cmd_args = cmd_obj[cmd_name]
                            cmd_callback(cmd_name, cmd_args)
                            buffer = ""
                        except json.JSONDecodeError:
                            # Handle parsing error
                            pass
            escape_next = False

    # Process any remaining command objects in the buffer
    if buffer:
        try:
            cmds = json.loads(buffer)
            for cmd_obj in cmds:
                cmd_name = next(iter(cmd_obj))
                cmd_args = cmd_obj[cmd_name]
                cmd_callback(cmd_name, cmd_args)
        except json.JSONDecodeError:
            # Handle parsing error
            pass

def chat_commands(model, prompt, cmd_callback=lambda cmd, **args: print(cmd, **args),
                  temperature=0, max_tokens=0, messages=[]):
    stream = stream_chat(model, prompt, temperature, max_tokens, messages)
    parse_cmd_stream(stream, cmd_callback)
