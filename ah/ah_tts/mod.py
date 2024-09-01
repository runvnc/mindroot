import torch
from TTS.api import TTS
from ..services import service

device = "cuda" if torch.cuda.is_available() else "cpu"

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

@service()
async def tts_to_wav_file(text, speaker_wav, language, file_path):
    wav = tts.tts_to_file(text=text, speaker_wav=speaker_wav, language=language, file_path=file_path)


