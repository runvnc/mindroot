from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter()

BASE_DIR = Path('/files/ah/personas')

@router.get('/personas/{scope}/{name}')
def read_persona(scope: str, name: str):
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    persona_path = BASE_DIR / scope / name / 'persona.json'
    if not persona_path.exists():
        raise HTTPException(status_code=404, detail='Persona not found')
    with open(persona_path, 'r') as f:
        return json.load(f)

@router.put('/personas/{scope}/{name}')
def update_persona(scope: str, name: str, persona: dict):
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    persona_path = BASE_DIR / scope / name / 'persona.json'
    if not persona_path.exists():
        raise HTTPException(status_code=404, detail='Persona not found')
    with open(persona_path, 'w') as f:
        json.dump(persona, f, indent=2)
    return {'status': 'success'}
