from pathlib import Path
import json
import logging
from fastapi import HTTPException
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_persona_from_index(index: str, persona: str):
    """Import a persona from the persona index.
    Args:
        index: Path to the persona index file
        persona: Name of the persona to import
    """
    print("import_persona_from_index")
    print("index = ", index)
    print("persona = ", persona)
    # copy dir from indices/{index}/personas/{persona}
    # to personas/local/{persona}
    index_path = Path('indices') / index / 'personas' / persona
    persona_path = Path('personas') / 'local' / persona
    print("Copying persona from", index_path, "to", persona_path)
    shutil.copytree(index_path, persona_path)
    
    logger.info(f"Successfully imported persona '{persona}' from index '{index}'")
    print("Successfully imported persona", persona, "from index", index)


def handle_persona_import(persona_data: dict, scope: str) -> str:
    """Handle importing a persona from embedded data in agent configuration.
    Returns the persona name to be used in agent configuration.
    
    Args:
        persona_data: Dictionary containing persona data or string with persona name
        scope: 'local' or 'shared'
        
    Returns:
        str: Name of the persona to reference in agent config
    """
    
    # If persona_data is already a string, just return it
    if isinstance(persona_data, str):
        return persona_data
        
    # Validate persona data
    if not isinstance(persona_data, dict):
        raise HTTPException(
            status_code=400,
            detail='Persona data must be either a string name or a dictionary'
        )
    
    persona_name = persona_data.get('name')
    if not persona_name:
        raise HTTPException(
            status_code=400,
            detail='Persona name required in persona data'
        )
    
    # Create persona path
    persona_path = Path('personas') / scope / persona_name / 'persona.json'
    
    # Check if persona already exists
    if persona_path.exists():
        logger.warning(f"Persona '{persona_name}' already exists in {scope} scope - skipping import")
        return persona_name
    
    try:
        # Create persona directory and save data
        persona_path.parent.mkdir(parents=True, exist_ok=True)
        with open(persona_path, 'w') as f:
            json.dump(persona_data, f, indent=2)
        
        logger.info(f"Successfully imported persona '{persona_name}' to {scope} scope")
        return persona_name
        
    except Exception as e:
        logger.error(f"Failed to import persona '{persona_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import persona: {str(e)}"
        )
