import os
import shutil
import json
from pathlib import Path


def init_models_and_providers():
    script_path = Path(__file__).parent
    models_path = Path("data")
    if not models_path.exists():
        os.mkdir(models_path)
 
    for file in script_path.glob("*.default.json"):
        dest = models_path / file.name.replace(".default.json", ".json")
        if not dest.exists():
            shutil.copy(file, dest)


def init_agents():
    script_path = Path(__file__).parent
    assistant = script_path / "Assistant"
    agents_path = Path("data/agents/local/")
    if not agents_path.exists():
        os.makedirs(agents_path)
    if not (agents_path / "Assistant").exists():
        shutil.copytree(assistant, agents_path / "Assistant")

init_models_and_providers()
init_agents()
