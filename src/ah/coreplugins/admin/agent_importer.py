from pathlib import Path
import json
import shutil
import logging
from typing import Dict, List
import os
import tempfile
import requests
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# These should be moved to a config file or environment variables
AGENT_BASE_DIR = Path('data/agents')
PERSONA_BASE_DIR = Path('personas')

CONFIRM_OVERWRITE_AGENT = os.environ.get('CONFIRM_OVERWRITE_AGENT', 'false')
if CONFIRM_OVERWRITE_AGENT.lower() in ['true', '1']:
    CONFIRM_OVERWRITE_AGENT = True
else:
    CONFIRM_OVERWRITE_AGENT = False

def download_github_files(repo_path: str, tag: str = None) -> tuple[str, str]:
    """Download GitHub repo files to temp directory"""
    # Format the download URL
    if tag:
        download_url = f"https://github.com/{repo_path}/archive/refs/tags/{tag}.zip"
    else:
        download_url = f"https://github.com/{repo_path}/archive/refs/heads/main.zip"
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'repo.zip')
    
    try:
        # Download the zip file
        response = requests.get(download_url)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        return temp_dir, os.path.dirname(zip_path)
            
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e

def scan_for_agents(directory: Path) -> Dict[str, Dict]:
    discovered_agents = {}
    for agent_file in directory.rglob('agent.json'):
        try:
            with agent_file.open('r') as f:
                agent_data = json.load(f)
            agent_name = agent_data.get('name')
            if agent_name:
                discovered_agents[agent_name] = {
                    'path': agent_file.parent,
                    'data': agent_data
                }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse agent file: {agent_file}")
        except PermissionError:
            logger.error(f"Permission denied when reading: {agent_file}")
    return discovered_agents

def validate_agent_structure(agent_data: Dict) -> bool:
    required_fields = ['name', 'persona', 'commands']
    return all(field in agent_data for field in required_fields)

def import_agent(agent_name: str, agent_info: Dict, scope: str) -> None:
    target_dir = Path(AGENT_BASE_DIR) / scope / agent_name
    if CONFIRM_OVERWRITE_AGENT and target_dir.exists():
        logger.warning(f"Agent {agent_name} already exists in {scope} scope, skipping")
        return
    
    if not validate_agent_structure(agent_info['data']):
        logger.error(f"Agent {agent_name} has invalid structure, skipping")
        return

    try:
        shutil.copytree(agent_info['path'], target_dir, dirs_exist_ok=True)
        logger.info(f"Imported agent {agent_name} to {target_dir}")

        persona_name = agent_info['data'].get('persona')
        if persona_name:
            persona_dir = os.path.join(agent_info['path'].parent.parent, "personas")
            import_persona(persona_name, persona_dir, scope)
    except PermissionError:
        logger.error(f"Permission denied when copying agent {agent_name}")
    except shutil.Error as e:
        logger.error(f"Error copying agent {agent_name}: {e}")

def import_persona(persona_name: str, source_dir: Path, scope: str) -> None:
    persona_source = Path(source_dir) / persona_name
    if not persona_source.exists():
        logger.warning(f"Referenced persona {persona_name} not found in {source_dir}")
        return
    
    persona_target = PERSONA_BASE_DIR / scope / persona_name
    if CONFIRM_OVERWRITE_AGENT and persona_target.exists():
        logger.warning(f"Persona {persona_name} already exists, skipping import")
        return
    
    try:
        shutil.copytree(persona_source, persona_target, dirs_exist_ok=True)
        logger.info(f"Imported persona {persona_name} to {persona_target}")
    except PermissionError:
        logger.error(f"Permission denied when copying persona {persona_name}")
    except shutil.Error as e:
        logger.error(f"Error copying persona {persona_name}: {e}")

def scan_and_import_agents(directory: Path, scope: str) -> Dict[str, List[str]]:
    if not directory.is_dir():
        raise ValueError(f"Invalid directory path: {directory}")
    
    if scope not in ['local', 'shared']:
        raise ValueError(f"Invalid scope: {scope}")
    
    discovered_agents = scan_for_agents(directory)
    
    imported_agents = []
    for agent_name, agent_info in discovered_agents.items():
        try:
            import_agent(agent_name, agent_info, scope)
            imported_agents.append(agent_name)
        except Exception as e:
            logger.error(f"Failed to import agent {agent_name}: {e}")
    
    return {
        'imported_agents': imported_agents,
        'total_imported': len(imported_agents),
        'total_discovered': len(discovered_agents)
    }

def import_github_agent(repo_path: str, scope: str, tag: str = None) -> Dict[str, any]:
    """Import an agent from a GitHub repository"""
    try:
        # Download and extract GitHub repository
        temp_dir, extract_path = download_github_files(repo_path, tag)
        
        try:
            # Scan the downloaded directory for agents
            discovered = scan_for_agents(Path(temp_dir))
            if not discovered:
                raise ValueError("No valid agents found in repository")
            
            # Import each discovered agent
            result = scan_and_import_agents(Path(temp_dir), scope)
            
            return {
                'success': True,
                'message': f"Successfully imported {result['total_imported']} agents from GitHub",
                'imported_agents': result['imported_agents']
            }
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"Failed to import agent from GitHub: {str(e)}")
        return {
            'success': False,
            'message': f"Failed to import agent: {str(e)}",
            'imported_agents': []
        }
