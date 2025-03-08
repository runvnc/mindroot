from lib.providers.commands import command, command_manager
from lib.providers.services import service_manager
from lib.chatcontext import ChatContext
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
            in the command array. Otherwise, be sure to issue the task_complete or similar
            command to indicate that the system should wait for the user reply.
            If you need the result of another command, do not end with task_complete.

    ## Example 1
   
   (in this example we issue multiple 'say' commands, but are finished with commands after that)

    [
        { "say": { "text": "Hello, user." } },
        { "say": { "text": "How can I help you today? } },
        { "task_complete": {} }
    ]

    (The system waits for the user reply)
   

    ## Example 2

    (In this example we issue a command and don't wait for the command result)

    [
        { "say": { "text": "Sure, I can run that command" } },
        { "execute_command": { "cmd": "update_db 3" } },
        { "task_complete": {} }
    ]

    ## Example 3

    (In this example we issue a command and wait for the result from the system)

    [
        { "say": { "text": "Sure, I can run that command" } },
        { "execute_command": { "cmd": "ls -l" } }
    ]


    (The system now returns the command output)


    ** Important Note **

    The say() command is a special type of command that stops after it is executed.
    That means, if you want to continue to do work, such as running another commmand
    after informing the user about your plans, it is CRITICAL that you place those
    commands in additional items in the same array.

    Otherwise, the system will stop and wait for the user to respond after each say() command.
    The say command is different from other commands in this way which would normally
    return a system acnknowledgement or result, allowing you to continue.

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

    Use the special RAW format with START_RAW and END_RAW to output raw markdown.

    Parameters:

    markdown - String. Insert using RAW mode.

    Note that you can use Katex for math rendering in markdown, but remember to
    use 'aligned' instead of 'align'. Always use 'math' code blocks for this.
    Be careful of limitations with KaTeX such as macros etc.

    Also, IMPORTANT: if you need to do other formatting in math sections such as
    a list of steps or a table, use the KaTeX formatting for this 
    rather than trying to add LaTeX in the middle of markdown lists
    or tables etc.

    Also, you can use HTML in the typical way it is inserted into markdown,
    including, for example, embedding YouTube videos.

    # Basic Example

        { "json_encoded_md":
          { "markdown": START_RAW
    ## Section 1

    - item 1
    - item 2
    END_RAW
          }
        }

    NOTE: Do NOT start a new command list if there already is one!!

    """
    #await context.agent_output("new_message", {"content": markdown,
    #                                        "agent": context.agent['name'] })

zz="""
Avoid putting LaTeX math expressions directly after list markers (1., -, *) - add some regular text first

    Avoid putting LaTeX math expressions at the very start of a line - add some text before it
"""

@command()
async def insert_image(image_url, context=None):
    await context.agent_output("image", {"url": image_url})


@command()
async def task_result(output: str, context=None):
    """
    Return the result of a task to the user.

    This should be the final output of a task that the user requested.

    Note: if you have this command defined, you MUST use it at the end of a task.
    Be sure to include the full output of the task, unless they specified 
    that they only want a brief or final answer.

    If you do not call this, the task will be repeated.

    Parameters:

    output - Array OR Object OR String. The output of the task, such as analysis, structured data,
    report, answer, etc.

    IMPORTANT: If the user requests JSON output or provides a schema, you must
    output ONLY the data in the format requested. 

    Unless otherwise indicated for your model, use the special 
    RAW format with START_RAW and END_RAW to output raw markdown.

    Example:

    User: Please output the addresses from the following document
        using this format (e.g.): 
        [{ "address1": "Main St.", "state": "CA", "zip: "90210" }]

        (... document ...)

    you would output something like this:

    { "task_result": {
        "output": [
            { "address1": "First St.", "state": "TX", "zip: "78573" },
            { "address2": "Second St.", "state": "TX", "zip: "78001" }
        ] }
    }

    ___


    In the case that the user requested a formatted report:

    Example:

    User: What is the answer to the universe?

    you would output something like this:

        { "task_result":
            { "output": START_RAW
    ## Answer
    
    The answer is 42.

    END_RAW

            }
        }

    """
    return None

@command()
async def initiate_agent_session(agent_name: str, context=None):
    """
    Initiate a chat session with another agent.
    IMPORTANT NOTE: You may not use this command while already in conversation with another agent.
    You must exit the current conversation and then the parent context will continue.

    Parameters:
    agent_name - String. The name of the agent to start a session with.

    Important: wait for the system to return the log_id for the new chat session before using the converse_with_agent() command.
    Return: String. The log_id for the new chat session.
    """
    log_id = nanoid.generate()
    user = context.username if 'username' in context else 'user'
    await init_chat_session(user, agent_name, log_id)
    
    return log_id


@command()
async def exit_conversation(output: str, context=None):
    """
    Exit a chat session with another agent. Use this when exit criteria are met.
    Use this command when you are finished with an agent. You may not initiate another conversation whie in a chat session with an agent.

    Parameters:
    output - String :
                        ALL relevant details of the conversation.
                        IMPORTANT: if the output of the conversation is a deliverable 
                        in the form of text, then depending on the wording of the user's  
                        instructions, you may need to include the ALL the text
                        of the deliverable here!
                        If the user asked for only a summary, then provide a summary.
                        If there was work output to a file, this must include the full filename. 
                        Etc.

                        This should be EVERY detail that is needed to continue, but none of 
                        any intermediary details of the conversation that aren't relevant.
                        Such as greetings, intermediary work steps, etc.
                        But assume that you will not be able to refer back to this conversation 
                        other than the takeaways listed here. So err on the side of caution of 
                        including MORE information. But be concise without losing ANY potentially 
                        relevant detail.

                        Example: discussion was about a shopping list that was requested from the user.
                        The output should be the full shopping list verbatim (but you can use abbreviations)

                        Example: discussion was about a long process ending in a file being created. 
                        The output should be the full filename and path.

                        Example: user requested to have an agent install some software. The output should be 
                        whether the software was successfully installed or not, and how to start and configure it.
                        The output in this case should not include all of the steps involved or files installed.
    """
    print('-------------------------------------------------------------------')
    print(context.log_id)
    print(termcolor.colored('exiting conversation', 'yellow', attrs=['bold']))
    print(termcolor.colored(output, 'yellow', attrs=['bold']))
    context.data['finished_conversation'] = True
    context.data['takeaways'] = output
    
    context.save_context()
    return output



@command()
async def converse_with_agent(agent_name: str, sub_log_id: str, first_message: str, contextual_info: str, exit_criteria: str, context=None):
    """
    IMPORTANT: Wait for the system to return the sub_log_id from the initiate_agent_session() command before using this command.
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
    
    finished_conversation = False
    my_sub_context.data['finished_conversation'] = False
    my_sub_context.save_context()

    takeaways = ""

    blank_my_replies = 0

    while not finished_conversation:
        if 'finished_conversation' not in my_sub_context.data:
            raise Exception("Error: 'finished_conversation' key not found in context.data " + str(my_sub_context))
        replies = []
        async with asyncio.timeout(1200.0):
            [_, replies] = await send_message_to_agent(sub_log_id, first_message)
        #print replies data for debugging, in magenta
        print(termcolor.colored('replies:', 'magenta', attrs=['bold']))
        print(termcolor.colored(replies, 'magenta', attrs=['bold']))

        async with asyncio.timeout(1200.0):
            [_, my_replies] = await send_message_to_agent(my_sub_log_id, f"[{agent_name}]: {json.dumps(replies)}")
            # print my_replies data for debugging, in cyan
            print(termcolor.colored('my_replies:', 'cyan', attrs=['bold']))
            print(termcolor.colored(my_replies, 'cyan', attrs=['bold']))

            if len(my_replies) == 0:
                blank_my_replies += 1
                if blank_my_replies > 3:
                    # print in red for debugging
                    print("Too many blank replies, exiting conversation")
                    break

        if my_sub_context.data['finished_conversation'] == True:
            takeaways = my_sub_context.data['takeaways']
            finished_conversation = True
            break
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

