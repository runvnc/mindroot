from ..services import service
from ..commands import command
import os
import json

@command()
async def think(extensive_chain_of_thoughts="", context=None):
    """
    Use chain-of-thought reasoning to think about the next thing to do or say systematically before additional commands or replies.
    This is also referred to as "system 2" thinking. You break down the problem, consider it carefully from multiple angles, 
    think step-by-step and show you work as you reason through a solution.

    If you use this command, you should have a substantial amount of thought.
    Do not simply write an introduction to the problem and move on.

    Always include other commands in the command array after this one.
    Note the use of escaped newlines in the thoughts parameter. 

    Remember, all commands must be valid JSON, which requires escaping newlines in strings.

    Parameters:

    extensive_chain_of_thoughts (str): The extensive thought process to consider before issuing additional commands.
                                       This must be at least 500 tokens long, otherwise the command will be rejected.

    Example (outline):

    [ { "think": { "extensive_chain_of_thoughts": "[Line 1]\n[Line 2]\n ..." } ]

    Think through the ENTIRE problem and compose and analyze your planned commands
    until you are satisfied that you have correctly finished.

    You should skip this for very trivial conversation turns that don't require reflection.

    But for anything non-trivial, if this command is available, utilize it thoroughly before outputting additional commands
    with replies to the user or actions.

    IMPORTANT: your thinking MUST:
    
    1. analyze HOW to approach the problem, considering multiple angles
    2. break down the problem into smaller parts
    3. consider the implications of each part
    4. drill into details of each part
    5. evaluate your final solution in reference to the original task
    6. make any improvements you can think of
    7. show your work as you go
    8. CRITICAL -- repeat all of the steps until you are truly certain you have refined as much as possible!!

    ALSO IMPORTANT: remember to escape newlines in your thoughts, to ensure valid JSON for the full comand list.

    The output commands after this should use work you have already prepared and considered carefully in this think() command.

    """
    return None
