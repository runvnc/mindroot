# look for data/models/models.json and providers.json
# if the directory does not exist, create it
# if the files do not exist, copy from [script_path]/models.default.json and [script_path]/providers.default.json

def init_models_and_providers():
    import os
    import shutil
    import json
    from pathlib import Path
    script_path = Path(__file__).parent
    models_path = Path("data/models")
    models_file = models_path / "models.json"
    providers_file = models_path / "providers.json"
    if not models_path.exists():
        os.mkdir(models_path)
    if not models_file.exists():
        shutil.copy(script_path / "models.default.json", models_file)
    if not providers_file.exists():
        shutil.copy(script_path / "providers.default.json", providers_file)
    with open(models_file) as f:
        models = json.load(f)
    with open(providers_file) as f:
        providers = json.load(f)
    return models, providers

init_models_and_providers()
