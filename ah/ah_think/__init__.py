from ..services import service
from ..commands import command
import os
import json

@command()
async def think(thoughts="", context=None):
    """Think about the next thing to do or say systematically before additional commands or replies.
       Always include other commands in the command array after this one.
       Note the use of escaped newlines in the thoughts parameter. 
    Remember, all commands must be valid JSON, which requires escaping newlines in strings.

    Parameters:

    thoughts (str): The thought process to consider before issuing additional commands.
    Example 1 (rough abstraction, not literal):

    [
    { "think": {"thoughts": "Since the user wants [X] and we currently know [Y], therefore [Z].\nThen assuming [Z], we will need to [1], [2]. The best way to [1] is ..." }} ,
    ]

    Actual thoughts will be entirely dependant upon the situation and conversation.
    You should skip this for very trivial conversation turns that don't require reflection.
    """
    return None
