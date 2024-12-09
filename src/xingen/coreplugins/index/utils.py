import json
import shutil
from pathlib import Path
from fastapi import HTTPException

async def load_persona_data(persona_name: str) -> dict:
    """Load persona data from local or shared directory"""
    try:
        persona_path = Path('personas/local') / persona_name / 'persona.json'
        if not persona_path.exists():
            persona_path = Path('personas/shared') / persona_name / 'persona.json'
            
        if not persona_path.exists():
            return {}
            
        with open(persona_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in persona file: {persona_name}")

async def load_agent_data(agent_name: str) -> dict:
    """Load agent data from local or shared directory"""
    try:
        agent_path = Path('data/agents/local') / agent_name / 'agent.json'
        if not agent_path.exists():
            agent_path = Path('data/agents/shared') / agent_name / 'agent.json'
            if not agent_path.exists():
                raise FileNotFoundError(f'Agent {agent_name} not found')
        
        with open(agent_path, 'r') as f:
            agent_data = json.load(f)
            
        # Validate required fields
        if 'name' not in agent_data:
            raise ValueError(f'Agent {agent_name} missing required field: name')
            
        # Get the persona data if specified
        if 'persona' in agent_data:
            persona_data = await load_persona_data(agent_data['persona'])
            agent_data['persona'] = persona_data
            
        return agent_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in agent file: {agent_name}")

def ensure_index_structure(index_dir: Path) -> None:
    """Ensure index directory has the required structure"""
    (index_dir / 'personas').mkdir(exist_ok=True)

def install_persona(source_dir: Path, persona_name: str) -> None:
    """Install a persona directory to the correct location"""
    target_dir = Path('personas/local') / persona_name
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir)
