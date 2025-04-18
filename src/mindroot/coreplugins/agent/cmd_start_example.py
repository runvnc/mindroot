from lib.providers.commands import command
import json

@command()
async def system_test(echo: str):
    """
    This is a test command that echoes the input string.
    Example:

    { "system_test": 
        { "echo": "Hello, World!" }
    }

    Example with multiline string:

    { "system_test": 
        { "echo": START_RAW
Hello, World!
Line 2
Line 3
END_RAW }
    }

    """
    return echo

def demo_boot_msgs():
    """
    We will insert a fake 'system test' command showing how the
    commands system works and how to format commands with multiline strings.
    """
    agent_test_msg = """
Agent online.
Verifying command format for embedding multiline strings."""
    sys_test = f"""
[
    {{ "system_test": 
        {{ "echo": START_RAW
{agent_test_msg}
END_RAW }}
    }}
]
        """

    sys_reply = {
        "SYSTEM": "",
        "cmd": "system_test",
        "args": {
            "omitted": "(see command msg.)"
        },
        "result": agent_test_msg
    }
    sys_reply = json.dumps(sys_reply)
    msgs = [
        {
            "role": "assistant",
            "content": [
                { "type": "text",
                  "text": sys_test
                }
            ]
        },
        {
            "role": "user",
            "content": [
                { "type": "text",
                  "text": sys_reply
                }
            ]
        }
    ]
    return msgs


