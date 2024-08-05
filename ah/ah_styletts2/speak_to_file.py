from styletts2 import tts
import wave
import numpy as np
import subprocess

SAMPLE_RATE = 24000
tts = tts.StyleTTS2()

def textToSpeech(text):
    voicewave = tts.inference(text,
                              diffusion_steps=20,
                              output_sample_rate=SAMPLE_RATE,
                              alpha=0.3,
                              beta=0.7,
                              embedding_scale=1.5
                              )
    return voicewave

def speak_to_file(text, filename):
    voicewave = textToSpeech(text)
    
    # Convert float32 array to int16
    voicewave_int = (voicewave * 32767).astype(np.int16)
    
    # Write to .wav file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 2 bytes for int16
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(voicewave_int.tobytes())
    
    # Open the file with xdg-open
    subprocess.run(['xdg-open', filename])

speak_to_file("Hello.", "/tmp/s2.wav")
speak_to_file("The quick brown fox jumped over the fence. ", "/tmp/s3.wav")
