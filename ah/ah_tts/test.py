from mod import tts_to_wav_file
import asyncio

async def test():
    await tts_to_wav_file("Hello there, how are you??", 'voice.wav', 'en', 'output1.wav')
    await tts_to_wav_file("There can only be one winner!", 'voice.wav', 'en', 'output2.wav')


# run test task
asyncio.run(test())
 
