from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path
import json

router = APIRouter()

BASE_DIR = Path('data/agents')
BASE_DIR.mkdir(parents=True, exist_ok=True)

@router.get('/agents/{scope}/{name}')
def read_agent(scope: str, name: str):
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    agent_path = BASE_DIR / scope / name / 'agent.json'
    if not agent_path.exists():
        raise HTTPException(status_code=404, detail='Agent not found')
    with open(agent_path, 'r') as f:
        agent = json.load(f)
    return agent

@router.get('/agents/{scope}')
def list_agents(scope: str):
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    scope_dir = BASE_DIR / scope
    agents = [p.name for p in scope_dir.iterdir() if p.is_dir()]
    return [{'name': name} for name in agents]

@router.post('/agents/{scope}')
def create_agent(scope: str, agent: str = Form(...), faceref: UploadFile = File(None), avatar: UploadFile = File(None)):
    try:
        agent = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
        agent_name = agent.get('name')
        if not agent_name:
            raise HTTPException(status_code=400, detail='Agent name is required')
        agent_path = BASE_DIR / scope / agent_name / 'agent.json'
        if agent_path.exists():
            raise HTTPException(status_code=400, detail='Agent already exists')
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        if faceref:
            faceref_path = agent_path.parent / 'faceref.png'
            with open(faceref_path, 'wb') as f:
                f.write(faceref.file.read())
            agent['faceref'] = str(faceref_path)
        if avatar:
            avatar_path = agent_path.parent / 'avatar.png'
            with open(avatar_path, 'wb') as f:
                f.write(avatar.file.read())
            agent['avatar'] = str(avatar_path)
        with open(agent_path, 'w') as f:
            json.dump(agent, f, indent=2)
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error ' + str(e))

@router.put('/agents/{scope}/{name}')
def update_agent(scope: str, name: str, agent: str = Form(...), faceref: UploadFile = File(None), avatar: UploadFile = File(None)):
    try:
        agent = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
        agent_path = BASE_DIR / scope / name / 'agent.json'
        if not agent_path.exists():
            raise HTTPException(status_code=404, detail='Agent not found')
        if faceref:
            faceref_path = agent_path.parent / 'faceref.png'
            with open(faceref_path, 'wb') as f:
                f.write(faceref.file.read())
            agent['faceref'] = str(faceref_path)
        if avatar:
            avatar_path = agent_path.parent / 'avatar.png'
            with open(avatar_path, 'wb') as f:
                f.write(avatar.file.read())
            agent['avatar'] = str(avatar_path)
        with open(agent_path, 'w') as f:
            json.dump(agent, f, indent=2)
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error ' + str(e))