from ..commands import command
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages
import asyncio
import json

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

async def collect_agent_replies(log_id: str, timeout: float = 120.0, max_replies: int = 5):
    """
    Helper function to collect replies from another agent in an existing conversation.
    """
    replies = []
    try:
        async with asyncio.timeout(timeout):
            async for event in subscribe_to_agent_messages(log_id):
                reply_data = json.loads(event['data'])
                replies.append(reply_data['content'])
                if len(replies) >= max_replies:
                    break
    except asyncio.TimeoutError:
        pass  # We've reached the timeout, stop collecting replies
    
    return replies

@command()
async def initiate_agent_session(agent_name: str, context=None):
    """
    Initiate a chat session with another agent.

    Parameters:
    agent_name - String. The name of the agent to start a session with.

    Return: String. The log_id for the new chat session.
    """
    log_id = await init_chat_session(agent_name, context)
    return log_id

@command()
async def communicate_with_agent(log_id: str, message: str, reply_timeout: float = 120.0, max_replies: int = 5, context=None):
    """
    Send a message to an agent in an existing chat session and collect replies.

    Parameters:
    log_id - String. The log_id of the existing chat session.
    message - String. The message to send to the agent.
    reply_timeout - Float. The maximum time to wait for replies, in seconds (default: 120.0 seconds).
    max_replies - Int. The maximum number of replies to collect.

    Return: Dict. Contains the sent message results and collected replies.
    """
    send_result = await send_message_to_agent(log_id, message)
    replies = await collect_agent_replies(log_id, reply_timeout, max_replies)
    
    return {
        "send_result": send_result,
        "replies": replies
    }
