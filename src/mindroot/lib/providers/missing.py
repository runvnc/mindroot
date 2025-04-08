import os
import re
import json
import inspect
from lib.providers.commands import command_manager
from lib.plugins.mapping import get_command_plugin_mapping


async def get_missing_commands(agent_name=None, context=None):
    """
    Identify commands that are used in agent instructions but not available in the system.
    
    Args:
        agent_name (str, optional): Name of the agent to check
        
    Returns:
        dict: Mapping of missing commands and potential plugins that provide them
    """
    if context and not agent_name:
        agent_name = context.agent_name
        
    if not agent_name:
        return {"error": "Agent name is required"}
    
    # Load agent data
    try:
        agent_path = f"data/agents/local/{agent_name}/agent.json"
        if not os.path.exists(agent_path):
            agent_path = f"data/agents/shared/{agent_name}/agent.json"
            
        if not os.path.exists(agent_path):
            return {"error": f"Agent {agent_name} not found"}
            
        with open(agent_path, 'r') as f:
            agent_data = json.load(f)
            
        # Get agent's command list
        agent_commands = agent_data.get('commands', [])
        
        # Get all available commands from the provider
        available_commands = set(command_manager.functions.keys())
        
        # Find commands mentioned in instructions but not available
        instructions = agent_data.get('instructions', '')
        
        # Extract command patterns like { "command_name": { ... } }
        command_pattern = r'{\s*"([a-zA-Z0-9_]+)"\s*:'
        mentioned_commands = set(re.findall(command_pattern, instructions))
        
        # Find commands that are mentioned but not available
        missing_commands = mentioned_commands - available_commands

        # Get command-plugin mapping
        command_plugin_mapping = await get_command_plugin_mapping()
        
        # Create result with missing commands and potential plugins
        result = {}
        for cmd in missing_commands:
            result[cmd] = command_plugin_mapping.get(cmd, [])
            
        return result
    except Exception as e:
        return {"error": str(e)}
