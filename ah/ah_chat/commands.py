from ..commands import command

@command()
async def say(text="", done=True, context=None):
    """
    Say something to the user or chat room.
    One sentence per command. If you want to say multiple sentences, use multiple commands.

    Parameters:
    text - String. The text to say.

    Return: No return value. To continue without waiting for user reply, add more commands  
            in the command array.

    ## Example 1
   
   (in this example we issue multiple 'say' commands, but are finished with commands after that)

    [
        { "say": { "text": "Hello, user." } },
        { "say": { "text": "How can I help you today? } }
    ]

    (The system waits for the user reply)
   

    ## Example 2

    (In this example we wait for the user reply before issuing more commands)

    [
        { "say": { "text": "Sure, I can run that command" } }
    ]

    (The system now waits for the user reply)

    """
    print("say command called, text = ", text, "done = ", done)
    await context.agent_output("new_message", {"content": text,
                               "agent": context.agent['name'] })
    return None

@command()
async def json_encoded_md(markdown="", context=None):
    """
    Output some markdown text to the user or chat room.
    Use this for any somewhat longer text that the user can read and
    and doesn't necessarily need to be spoken out loud.

    You can write as much text/sentences etc. as you need.

    IMPORTANT: make sure everything is properly encoded as this is a JSON 
    command (such as escaping double quotes, escaping newlines, etc.)

    Parameters:

    markdown - String.  MUST BE PROPERLY JSON-encoded string! E.g. escape all double quotes, newlines, etc.

    # Example

    [
        { "json_encoded_md": { "markdown": "## Section 1\\n\\n- item 1\\n- item 2" } }
    ]

    # Example

    [
        { "json_encoded_md": { "markdown": "Here is a list:\\n\\n- item 1\\n- item 2\\n- line 3" }} 
    ]

    """
    await context.agent_output("new_message", {"content": markdown,
                                            "agent": context.agent['name'] })

@command()
async def insert_image(image_url, context=None):
    await context.agent_output("image", {"url": image_url})
