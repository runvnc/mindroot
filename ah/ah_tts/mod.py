import torch
from TTS.api import TTS
from ..services import service
from ..commands import command
import nanoid
import os

device = "cuda" if torch.cuda.is_available() else "cpu"

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

@service()
async def text_to_wav_file(text, speaker_wav, language, out_wav_file):
    wav = tts.tts_to_file(text=text, speaker_wav=speaker_wav, language=language, file_path=out_wav_file)

import asyncio
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
    # get voice.wav from same dir as script file_path
    script_path = __file__
    rnd_tmp_file = "/tmp/" + nanoid.generate() + ".wav"
    #voice_file = script_path.replace("mod.py", "voice.wav")
    voice_file = os.environ.get("AH_DEFAULT_VOICE")
    voice_file2 = os.environ.get("AH_DEFAULT_VOICE2")
    #voice_file = None
    await text_to_wav_file(text, [voice_file, voice_file2], "en", rnd_tmp_file)
    # play in background with aplay
    os.system("aplay " + rnd_tmp_file)
    await context.agent_output("new_message", {"content": text,
                               "agent": context.agent['name'] })
    await asyncio.sleep(0.05)
    return None


