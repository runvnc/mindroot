# look for data/models/models.json and providers.json
# if the directory does not exist, create it
# if the files do not exist, copy from [script_path]/models.default.json and [script_path]/providers.default.json

def init_models_and_providers():
    import os
    import shutil
    import json
    from pathlib import Path
    script_path = Path(__file__).parent
    models_path = Path("data")
    if not models_path.exists():
        os.mkdir(models_path)
 
    for file in script_path.glob("*.default.json"):
        dest = models_path / file.name.replace(".default.json", ".json")
        if not dest.exists():
            shutil.copy(file, dest)


init_models_and_providers()
