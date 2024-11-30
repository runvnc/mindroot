import os
import shutil
import json
from pathlib import Path


def init_persona():
    script_path = Path(__file__).parent
    assistant = script_path / "Assistant"
    personas_path = Path("personas/local/")
    if not personas_path.exists():
        os.makedirs(personas_path)
    if not (personas_path / "Assistant").exists():
        shutil.copytree(assistant, personas_path / "Assistant")

init_persona()
