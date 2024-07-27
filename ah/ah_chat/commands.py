from ..commands import command, command_manager
from ..services import service_manager
from ..chatcontext import ChatContext
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages
import asyncio
import json
import nanoid


@command()
async def say(text="", context=None):
    """
    Say something to the user or chat room.
    One sentence per command. If you want to say multiple sentences, use multiple commands.

    Parameters:
    text - String. The text to say.

    Return: No return value. To continue without waiting for user reply, add more commands  
            in the command array. Otherwise, the system will stop and wait for user reply!

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
    print("say command called, text = ", text)
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

async def collect_agent_replies(log_id: str, timeout: float = 240.0, max_replies: int = 10):
    """
    Helper function to collect replies from another agent in an existing conversation.
    """
    replies = []
    subscription = subscribe_to_agent_messages(log_id)

    try:
        async with asyncio.timeout(timeout):
            async for event in subscription:
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
    log_id = nanoid.generate()
 
    await init_chat_session(agent_name, log_id)
    return log_id


@command()
async def exit_conversation(takeaways: str, context=None):
    """
    Exit a chat session with another agent. Use this when exit criteria are met.

    Parameters:
    takeaways - String. A concise summary of relevant details of the conversation.

    """
    context.data['finished_conversation'] = True
    return takeaways

# have agent conversation with another agent
# bring in recent messages from this context/log  but not all messages
# specify the most important agenda items for the conversation
#

# chat logs:

# 1. system -> supervistor agent : when user initiates a task, system initiates chat with supervisor agent
#  this is the parent chat log
# 2. supervisor agent -> worker agent: supervisor agent initiates chat with worker agent given the task and (if any) recent messages
#    this goes in a new chat log which for the supervisor which contains recent messages and task but not all messages
# 3. supervisor agent -> worker agent from worker's perspective: another chat log that contains only the message from the worker's perspective
#  starting with the supervisor's first message
#

# supervisor agent chat goes in loop until supervisor calls exit_chat and returns a concise but complete summary of the relevant conversation
# details  

# the parent chat log is continued with the output of the conversation being added as a "user" system message and then
# the supervisor decides what to do next such as recording the task as completed or moving on to another worker

@command()
async def converse_with_agent(agent_name: str, sub_log_id: str, first_message: str, contextual_info: str, exit_criteria: str, context=None):
    """
    Have a conversation with an agent in an existing chat session.
    Note: once you start the conversation, use normal Say commands etc. to coninue the conversation.
        do not use this command again to send messages to the agent. 

    Parameters:
    agent_name - String. The name of the agent to converse with.
    sub_log_id - String. The log_id of the existing chat session with a secondary agent.
    IMPORTANT: this is NOT the agent name. It is the log_id/session_id of the chat session.

    first_message - String. The first message to the agent.
    contextual_info - String. Relevant details that may come up.
    exit_criteria - String. The criteria for ending the conversation.

    Return: String. Contains a concise summary of relevant details of conversation.
    """
    # create a temp chat log for the agent's perspective on this subconversation
    my_sub_log_id = nanoid.generate()
    print('-------------------------------------------------------------------')
    print('===================================================================')
    print(context, context.agent_name)
    await init_chat_session(context.agent_name, my_sub_log_id)
    my_sub_context = ChatContext(service_manager, command_manager)
    await my_sub_context.load_context(my_sub_log_id)
    
    my_sub_log = my_sub_context.chat_log

    to_exit = f"Context: {contextual_info}\n\n Conversation exit criteria: {exit_criteria}.\n\n When exit_criteria met, use the exit_conversation() command specifying concise detailed takeaways."
    init_sub_msg = f"[SYSTEM]: Initiating chat session with [{my_sub_context.agent_name}] taking User role... " + to_exit
    my_sub_log.add_message({"role": "user", "content": init_sub_msg})
    my_sub_log.add_message({"role": "assistant", "content": f"[{agent_name}]:" + first_message})
    
    sub_agent_replies = await subscribe_to_agent_messages(sub_log_id)
    finished_conversation = False
    my_sub_context.data['finished_conversation'] = False

    my_sub_replies = await subscribe_to_agent_messages(my_sub_log_id)
    print('######################################################################################')

    while not finished_conversation:
        replies = []
        run_sub_agent = asyncio.create_task(send_message_to_agent(sub_log_id, first_message))
        async with asyncio.timeout(12.0):
            async for event in sub_agent_replies:
                print(event)
                if event['event'] == 'running_command':
                    reply_data = json.loads(event['data'])
                    print('reply_data:', reply_data)
                    replies.append(reply_data)
                if run_sub_agent.done():
                    print("run_sub_agent done")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    break
                print("Waiting for sub-agent replies...")
        await run_sub_agent
        print("Sending replies to parent agent...")
        print('oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo OK done')
        # make sure to flush output with option
        print(",", flush=True)
        finished_conversation = True
        #x = """
        run_parent_agent = asyncio.create_task(send_message_to_agent(my_sub_log_id, f"[agent_name]: {json.dumps(replies)}"))
        my_replies = []
        print("////////////////////////////////////////////////////////////////////////////////////////////////////////////")
        async with asyncio.timeout(12.0):
            async for event2 in my_sub_replies:
                print(event2)
                if event2['event'] == 'running_command':
                    reply_data = json.loads(event['data'])
                    print('reply_data:', reply_data)
                    my_replies.append(reply_data)
                asyncio.sleep(0.1)
                if run_parent_agent.done():
                    break
        print("Waiting for parent agent replies...")
        await run_parent_agent
        #"""
        print(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
        print("my_replies:", my_replies)
        #if my_sub_context.data['finished_conversation']:
        #    finished_conversation = True
        #else:
        #    first_message = json.dumps(my_replies)
         
    return {
        f"[SYSTEM]: Exited conversation with {agent_name}. {agent_name} replies were:": replies
    }
