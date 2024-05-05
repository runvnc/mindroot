import asyncio
import json
from use_ollama import stream_chat, list
from ollama import AsyncClient

async def parse_cmd_stream(stream, cmd_callback=None):
    buffer = ""
    stack = []
    in_string = False
    escape_next = False

    async for part in stream:
        chunk = part['message']['content']
        print(chunk, flush=True, end='')
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

async def chat_commands(model, cmd_callback=None,
                  temperature=0, max_tokens=0, messages=[]):
    stream = await stream_chat(model,
                         temperature=temperature,
                         max_tokens=max_tokens,
                         messages=messages)
    await parse_cmd_stream(stream, cmd_callback)


async def show_models():
    print(await list())

async def simple_test_1():
  message = {'role': 'user', 'content': 'Why is the sky blue?'}
  async for part in await AsyncClient().chat(model='phi3', messages=[message], stream=True):
    print(part['message']['content'], end='', flush=True)
    

def do_print(cmd, *args):
    print(*args)

if __name__ == "__main__":

    cmds = [ {  "say": { "descr": "Output text (possibly spoken) to the user", 
                         "examples": [ { "say": "Hello, user." }]
                       }
             } ]

    cmds_json = json.dumps(cmds, indent=4) 

    sys = f""" 
# Core

You are an advanced AI agent. You output commands in a JSON format as an array.
You never output commentary outside of the command format.

# Available commands 

Commands allowed: "say" -- one sentence per say command, multiple say commands allowed!

# Example Interaction

User: Hello there.

Assistant: [ {{"say": "Hello user, this is the first line."}},
             {{"say": "This is the second thing I wanted to say -- how are you?"}} ]

# Notice

Respond with JSON array ONLY using commands from Available Commands above, such as the say command.

        """

    messages = [{ "role": "system", "content": sys},
                { "role": "user", "content": "Please write a short poem about the moon." }]
    print(messages)
    asyncio.run(chat_commands("phi3", messages=messages, cmd_callback=do_print))
    #asyncio.run(show_models())
    #asyncio.run(simple_test_1())

