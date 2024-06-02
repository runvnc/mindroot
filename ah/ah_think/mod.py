from ..services import service
from ..commands import command
import os
import json

@command(is_local=False)
async def think(thought_process, context=None):
    """Think about the next thing to do or say systematically before additional commands or replies.

    Returns: None

    You should issue other commands or output after this command.

    Example (rough abstraction, not literal):

    [
    { "think": "Since the user wants [X] and we currently know [Y], therefore [Z]. Then assuming [Z], we will need to [1], [2]. The best way to [1] is ..." },
    { "say": "Here is the plan I have come up with [...]" }
    ]

    Actual thoughts will be entirely dependant upon the situation and conversation.
    You should skip this for very trivial conversation turns that don't require reflection.
    """
    #await context.agent_output("thought", {"content": assistant_message,
    #                                           "persona": persona_['name'] })
    json_cmd = { "think": thought_process }
    context.chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})
  
