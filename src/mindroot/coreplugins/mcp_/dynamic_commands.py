from typing import Dict, List, Any
import json
import inspect
from lib.providers.commands import command_manager

class MCPDynamicCommands:
    """Handles dynamic registration of MCP tools as MindRoot commands"""
    
    def __init__(self):
        self.registered_commands: Dict[str, str] = {}  # cmd_name -> server_name
        self.sessions: Dict[str, Any] = {}  # Reference to sessions
    
    def set_sessions(self, sessions: Dict[str, Any]):
        """Set reference to MCP sessions"""
        self.sessions = sessions
    
    async def register_tools(self, server_name: str, tools: List[Any]):
        """Register MCP tools as dynamic MindRoot commands"""
        for tool in tools:
            try:
                tool_name = tool.name
                #cmd_name = f"mcp_{server_name}_{tool_name}"
                cmd_name = "mcp_"+tool_name
 
                self.registered_commands[cmd_name] = server_name
                
                # Create wrapper function with closure to capture current values
                def create_wrapper(srv_name, tl_name):
                    async def mcp_tool_wrapper(*args, context=None, **kwargs):
                        if srv_name not in self.sessions:
                            return f"MCP server {srv_name} not connected"
                        
                        session = self.sessions[srv_name]
                        
                        # Convert arguments to MCP format
                        if len(args) == 1 and isinstance(args[0], dict):
                            arguments = args[0]
                        elif kwargs:
                            # Filter out context from kwargs
                            arguments = {k: v for k, v in kwargs.items() if k != 'context'}
                        else:
                            arguments = {}
                        
                        try:
                            result = await session.call_tool(tl_name, arguments)
                            
                            # Extract content from CallToolResult object
                            if hasattr(result, 'content'):
                                if isinstance(result.content, list) and len(result.content) > 0:
                                    # Return the text content of the first item
                                    first_item = result.content[0]
                                    return first_item.text if hasattr(first_item, 'text') else str(first_item)
                                else:
                                    return str(result.content)
                            else:
                                return str(result)
                        except Exception as e:
                            return f"Error calling MCP tool {tl_name}: {str(e)}"
                    
                    return mcp_tool_wrapper
                
                wrapper = create_wrapper(server_name, tool_name)
                
                # Create docstring with parameter information
                description = getattr(tool, 'description', 'No description available')
                
                # Extract parameter schema if available
                param_info = ""
                example_args = {}
                
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    schema = tool.inputSchema
                    if isinstance(schema, dict) and 'properties' in schema:
                        properties = schema['properties']
                        required = schema.get('required', [])
                        
                        param_lines = []
                        for param_name, param_def in properties.items():
                            param_type = param_def.get('type', 'any')
                            param_desc = param_def.get('description', '')
                            is_required = param_name in required
                            req_text = ' (required)' if is_required else ' (optional)'
                            param_lines.append(f"  {param_name} ({param_type}){req_text}: {param_desc}")
                            
                            # Create example value based on type
                            if param_type == 'string':
                                example_args[param_name] = f"example_{param_name}"
                            elif param_type == 'number':
                                example_args[param_name] = 42
                            elif param_type == 'boolean':
                                example_args[param_name] = True
                            else:
                                example_args[param_name] = f"value_for_{param_name}"
                        
                        if param_lines:
                            param_info = "\n\nParameters:\n" + "\n".join(param_lines)
                
                # Use actual parameter names in example if available
                example_json = json.dumps(example_args, indent=2) if example_args else '{"arg1": "value1"}'
                
                docstring = f"""MCP Tool: {tool_name} from {server_name}

{description}{param_info}

{description}

Example:
{{ "{cmd_name}": {example_json} }}
"""
                
                # Register with command manager
                try:
                    command_manager.register_function(
                        name=cmd_name,
                        provider="mcp",
                        implementation=wrapper,
                        signature=inspect.signature(wrapper),
                        docstring=docstring,
                        flags=[]
                    )
                    print(f"Registered MCP command: {cmd_name}")
                    
                    # Verify registration
                    if cmd_name in command_manager.functions:
                        print(f"  ✅ Verified: {cmd_name} is in command manager")
                    else:
                        print(f"  ❌ Warning: {cmd_name} not found in command manager after registration")
                except Exception as e:
                    print(f"Error registering {cmd_name}: {e}")
                    
            except Exception as e:
                print(f"Error processing tool {getattr(tool, 'name', 'unknown')}: {e}")
                continue
    
    async def unregister_server_tools(self, server_name: str):
        """Unregister all tools for a server"""
        commands_to_remove = []
        for cmd_name, srv_name in self.registered_commands.items():
            if srv_name == server_name:
                commands_to_remove.append(cmd_name)
        
        for cmd_name in commands_to_remove:
            try:
                if cmd_name in command_manager.functions:
                    del command_manager.functions[cmd_name]
                del self.registered_commands[cmd_name]
                print(f"Unregistered MCP command: {cmd_name}")
            except Exception as e:
                print(f"Error unregistering {cmd_name}: {e}")
    
    def get_registered_commands(self) -> List[str]:
        """Get list of registered command names"""
        return list(self.registered_commands.keys())

