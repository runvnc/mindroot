import subprocess
import asyncio
from typing import Dict, Optional

class MCPServerInstaller:
    """Handles installation of MCP servers via different methods"""
    
    @staticmethod
    async def check_tools() -> Dict[str, bool]:
        """Check if installation tools are available"""
        tools = {}
        
        for tool in ['uvx', 'npx', 'npm', 'pip']:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                tools[tool] = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                tools[tool] = False
        
        return tools
    
    @staticmethod
    async def install_with_uvx(package: str, args: list = None) -> bool:
        """Install package with uvx"""
        if args is None:
            args = []
        
        try:
            # For uvx, we don't need to install, just check if it can run
            cmd = ['uvx', '--help']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"Error with uvx: {e}")
            return False
    
    @staticmethod
    async def install_with_npx(package: str, args: list = None) -> bool:
        """Install package with npx (similar to uvx, runs without global install)"""
        if args is None:
            args = []
        
        try:
            # For npx, we don't need to install, just check if it can run
            cmd = ['npx', '--help']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"Error with npx: {e}")
            return False
    
    @staticmethod
    async def install_with_pip(package: str, args: list = None) -> bool:
        """Install package with pip"""
        if args is None:
            args = []
        
        try:
            cmd = ['pip', 'install'] + args + [package]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except Exception as e:
            print(f"Error installing with pip: {e}")
            return False
    
    @staticmethod
    async def install_with_npm(package: str, args: list = None) -> bool:
        """Install package with npm"""
        if args is None:
            args = []
        
        try:
            cmd = ['npm', 'install', '-g'] + args + [package]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode == 0
        except Exception as e:
            print(f"Error installing with npm: {e}")
            return False