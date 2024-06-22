from ..services import service
from ..commands import command
import os
import json

@command()
async def think(thoughts="", done=False, context=None):
    """Think about the next thing to do or say systematically before additional commands or replies.

    Parameters:

    thoughts (str): The thought process to consider before issuing additional commands.
    done (bool): If false, the system will respond expecting the next command(s)
    If true, the system will stop after this command and wait for the user to reply.
    
    Returns: str: either "stop" or "continue" to indicate whether the system should continue or stop after this command.

    If you specify should_continue: true, then you should issue other commands or output after this command.

    Example 1 (rough abstraction, not literal):

    [
    { "think": {"thoughts": "Since the user wants [X] and we currently know [Y], therefore [Z]. Then assuming [Z], we will need to [1], [2]. The best way to [1] is ...", "done": false }} ,
    ]

    ( System responds with "continue" )

    [
    { "say": {"text": "Here is the plan I have come up with [...]", "done": true } }
    ] 

    ( System waits for user reply )

    Example 2 (rough abstraction, not literal):

    [
    { "think": {"thoughts": "Since the user wants [X] and we currently know [Y], therefore [Z]. Then assuming [Z], we will need to [1], [2]. The best way to [1] is ...", "done": true } } ,
    { "say": {"text": "Here is the plan I have come up with [...]", "done": true } }
    ]

    ( System waits for user reply )

    Actual thoughts will be entirely dependant upon the situation and conversation.
    You should skip this for very trivial conversation turns that don't require reflection.
    """
    #await context.agent_output("thought", {"content": assistant_message,
    #                                           "persona": persona_['name'] })
    #json_cmd = { "think": { thoughts } }
    #context.chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})
    if done:
        return 'stop'
    else:
        return 'continue'

