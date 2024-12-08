import json
import shutil
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from ..models import AgentEntry
from ..utils import load_agent_data

async def add_agent(INDEX_DIR: Path, index_name: str, agent: AgentEntry):
    """Add an agent to an index"""
    try:
        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        if not index_file.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        try:
            agent_data = await load_agent_data(agent.name)
        except FileNotFoundError as e:
            return JSONResponse({'success': False, 'message': str(e)})
        except ValueError as e:
            return JSONResponse({'success': False, 'message': str(e)})

        agent_data['added_at'] = datetime.now().isoformat()
        
        with open(index_file, 'r') as f:
            index_data = json.load(f)

        if any(a['name'] == agent.name for a in index_data['agents']):
            return JSONResponse({'success': False, 'message': 'Agent already in index'})

        # Copy agent directory structure to index
        agent_source = Path('data/agents/local') / agent.name
        if not agent_source.exists():
            agent_source = Path('data/agents/shared') / agent.name

        agent_target = index_dir / 'agents' / agent.name
        if agent_target.exists():
            shutil.rmtree(agent_target)
        shutil.copytree(agent_source, agent_target)

        # If agent has a persona, copy that too
        if 'persona' in agent_data and isinstance(agent_data['persona'], dict):
            persona_name = agent_data['persona'].get('name')
            if persona_name:
                persona_source = Path('personas/local') / persona_name
                if not persona_source.exists():
                    persona_source = Path('personas/shared') / persona_name
                if persona_source.exists():
                    persona_target = index_dir / 'personas' / persona_name
                    if persona_target.exists():
                        shutil.rmtree(persona_target)
                    shutil.copytree(persona_source, persona_target)

        index_data['agents'].append(agent_data)

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def remove_agent(INDEX_DIR: Path, index_name: str, agent_name: str):
    """Remove an agent from an index"""
    try:
        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        if not index_file.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(index_file, 'r') as f:
            index_data = json.load(f)

        # Get agent data before removal to handle persona cleanup
        agent_data = next((a for a in index_data['agents'] if a['name'] == agent_name), None)
        if agent_data and 'persona' in agent_data:
            persona_name = agent_data['persona'].get('name')
            if persona_name:
                persona_dir = index_dir / 'personas' / persona_name
                if persona_dir.exists():
                    # Check if persona is used by other agents before removing
                    other_agents_with_persona = [a for a in index_data['agents'] 
                                                if a['name'] != agent_name 
                                                and a.get('persona', {}).get('name') == persona_name]
                    if not other_agents_with_persona:
                        shutil.rmtree(persona_dir)

        index_data['agents'] = [a for a in index_data['agents'] if a['name'] != agent_name]

        # Remove agent directory
        agent_dir = index_dir / 'agents' / agent_name
        if agent_dir.exists():
            shutil.rmtree(agent_dir)

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
