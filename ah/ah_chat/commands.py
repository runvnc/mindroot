from ..commands import command, command_manager
from ..services import service_manager
from ..chatcontext import ChatContext
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages
import asyncio
import json
import nanoid
import termcolor

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
    print('-------------------------------------------------------------------')
    print(context.log_id)
    print(termcolor.colored('exiting conversation', 'yellow', attrs=['bold']))
    print(termcolor.colored(takeaways, 'yellow', attrs=['bold']))
    context.data['finished_conversation'] = True
    context.data['takeaways'] = takeaways
    context.save_context()
    return takeaways

@command()
async def converse_with_agent(agent_name: str, sub_log_id: str, first_message: str, contextual_info: str, exit_criteria: str, context=None):
    """
    Have a conversation with an agent in an existing chat session.
    Note:
        Do not use this command again to send more messages to the agent. 
        Again, IMPORTANT: do NOT use this command from within a subconversation.
        You only issue this command ONCE, then the conversation occurs in another subcontext.

    Parameters:
    agent_name - String. The name of the agent to converse with.
    sub_log_id - String. The log_id of the existing chat session with a secondary agent.

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
    my_sub_context.data['parent_log_id'] = context.log_id
    my_sub_log = my_sub_context.chat_log

    to_exit = f"Context: {contextual_info}\n\n Conversation exit criteria: {exit_criteria}.\n\n When exit_criteria met, use the exit_conversation() command specifying concise detailed takeaways."
    init_sub_msg = f"[SYSTEM]: Initiating chat session with [{my_sub_context.agent_name}] taking User role... \n\n" + to_exit
    my_sub_log.add_message({"role": "user", "content": init_sub_msg})
    my_sub_log.add_message({"role": "assistant", "content": f"[{agent_name}]:" + first_message})
    
    sub_agent_replies = await subscribe_to_agent_messages(sub_log_id)
    finished_conversation = False
    my_sub_context.data['finished_conversation'] = False

    my_sub_replies = await subscribe_to_agent_messages(my_sub_log_id)
    print('######################################################################################')
    takeaways = ""

    while not finished_conversation:
        # make sure that 'finished_conversation' key is in the context.data
        if 'finished_conversation' not in my_sub_context.data:
            throw("Error: 'finished_conversation' key not found in context.data " + str(my_sub_context))
        replies = []
        async with asyncio.timeout(120.0):
            replies = await send_message_to_agent(sub_log_id, first_message)
        print("Sending replies to supervisor agent...")
        print('oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo OK done')
        print(",", flush=True)
        print("////////////////////////////////////////////////////////////////////////////////////////////////////////////")

        async with asyncio.timeout(120.0):
            my_replies = await send_message_to_agent(my_sub_log_id, f"[agent_name]: {json.dumps(replies)}")
        print("Waiting for parent agent replies...")
        #"""
        print(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
        print("my_replies:", my_replies)
        if my_sub_context.data['finished_conversation'] == True:
            takeaways = my_sub_context.data['takeaways']
            finished_conversation = True
        else:
            first_message = json.dumps(my_replies)
        print("End of loop")
        sub_context = ChatContext(service_manager, command_manager)
        await sub_context.load_context(sub_log_id)
        await my_sub_context.load_context(my_sub_log_id)
  
        print(termcolor.colored('my_sub_context.data:', 'blue', attrs=['bold']))
        print(termcolor.colored(my_sub_context.data, 'blue', attrs=['bold']))
        print(termcolor.colored('sub_context.data:', 'blue', attrs=['bold']))
        print(termcolor.colored(sub_context.data, 'blue', attrs=['bold']))
         
    return {
        f"[SYSTEM]: Exited conversation with {agent_name}. {agent_name} takeaways were:": takeaways
    }


@command()
async def send_to_parent_chat(message: str, context=None):
    """
    Send a message to the parent chat session.
    This must only be used within a subconversation initiated by converse_with_agent().
    It is useful for things like informing the user about task status or requesting that the user provide a file, etc.

Parameters:
    message - String. The message to send to the parent chat session.
    Return: None
    """
    parent_log = context.data['parent_log_id']
    parent_context = ChatContext(service_manager, command_manager)
    await parent_context.load_context(parent_log)
    chat_log.add_message({"role": "assistant", "content": message})
    await agent_output("new_message", {"content": message, "agent": context.agent['name']})
    chat_log = parent_context.chat_log
    return None

