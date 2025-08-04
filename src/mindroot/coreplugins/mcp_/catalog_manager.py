import json
import os
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

class MCPCatalogManager:
    """Manages MCP server catalog and process detection"""
    
    def __init__(self, plugin_dir: str = None, working_dir: str = None):
        # Default plugin_dir to the directory containing this module
        if plugin_dir is None:
            plugin_dir = Path(__file__).parent.parent.parent
        self.plugin_dir = Path(plugin_dir)
        
        # Use process working directory for data files
        if working_dir is None:
            working_dir = os.getcwd()
        self.working_dir = Path(working_dir)
        
        self.catalog_file = self.working_dir / "data" / "mcp" / "servers.json"
        self.default_file = Path(__file__).parent / "data" / "default_mcp_servers.json"
        self.ensure_catalog_exists()
        
    
    def ensure_catalog_exists(self):
        """Ensure catalog file exists, create from default if needed"""
        if not self.catalog_file.exists():
            if self.default_file.exists():
                self.init_catalog_from_default()
            else:
                self.create_empty_catalog()
    
    def init_catalog_from_default(self):
        """Initialize catalog from default servers"""
        # Ensure the target directory exists
        self.catalog_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.default_file, 'r') as f:
                default_servers = json.load(f)
            
            catalog = {
                "_metadata": {
                    "version": "1.0.0",
                    "last_updated": "2025-06-02",
                    "description": "MCP Server Catalog for MindRoot",
                    "categories": ["utilities", "system", "development", "search", "database", "communication", "cloud", "automation", "ai"]
                },
                "servers": {}
            }
            
            for name, server in default_servers.items():
                server["status"] = "available"
                server["installed"] = False
                server["running"] = False
                catalog["servers"][name] = server
            
            with open(self.catalog_file, 'w') as f:
                json.dump(catalog, f, indent=2)
                
        except Exception as e:
            print(f"Error initializing catalog: {e}")
            self.create_empty_catalog()
    
    def create_empty_catalog(self):
        """Create empty catalog structure"""
        catalog = {
            "_metadata": {
                "version": "1.0.0",
                "last_updated": "2025-06-02",
                "description": "MCP Server Catalog for MindRoot",
                "categories": []
            },
            "servers": {}
        }
        
        self.catalog_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.catalog_file, 'w') as f:
            json.dump(catalog, f, indent=2)
    
    def load_catalog(self) -> Dict[str, Any]:
        """Load the server catalog"""
        try:
            with open(self.catalog_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading catalog: {e}")
            return {"_metadata": {}, "servers": {}}
    
    def save_catalog(self, catalog: Dict[str, Any]):
        """Save the server catalog"""
        try:
            with open(self.catalog_file, 'w') as f:
                json.dump(catalog, f, indent=2)
        except Exception as e:
            print(f"Error saving catalog: {e}")
    
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes with details"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': proc.info['cmdline'] or []
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting processes: {e}")
        
        return processes
    
    def detect_running_servers(self) -> Dict[str, bool]:
        """Detect which MCP servers are currently running"""
        catalog = self.load_catalog()
        running_status = {}
        processes = self.get_running_processes()
        
        for server_name, server_info in catalog.get("servers", {}).items():
            is_running = False
            process_names = server_info.get("process_names", [])
            
            for proc in processes:
                # Check process name
                if proc['name'] in process_names:
                    is_running = True
                    break
                
                # Check command line for MCP server patterns
                cmdline_str = ' '.join(proc['cmdline'])
                for process_name in process_names:
                    if process_name in cmdline_str:
                        is_running = True
                        break
                
                # Check for specific patterns
                if server_name in cmdline_str or server_info.get('install_package', '') in cmdline_str:
                    is_running = True
                    break
                
                if is_running:
                    break
            
            running_status[server_name] = is_running
        
        return running_status
    
    def update_server_status(self):
        """Update running status for all servers in catalog"""
        catalog = self.load_catalog()
        running_status = self.detect_running_servers()
        
        for server_name, is_running in running_status.items():
            if server_name in catalog.get("servers", {}):
                catalog["servers"][server_name]["running"] = is_running
        
        self.save_catalog(catalog)
        return catalog
    
    def get_servers_by_category(self, category: str = None) -> Dict[str, Any]:
        """Get servers filtered by category"""
        catalog = self.load_catalog()
        servers = catalog.get("servers", {})
        
        if category is None:
            return servers
        
        filtered = {}
        for name, server in servers.items():
            if server.get("category") == category:
                filtered[name] = server
        
        return filtered
    
    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific server"""
        catalog = self.load_catalog()
        return catalog.get("servers", {}).get(server_name)
    
    def mark_server_installed(self, server_name: str, installed: bool = True):
        """Mark a server as installed or not"""
        catalog = self.load_catalog()
        if server_name in catalog.get("servers", {}):
            catalog["servers"][server_name]["installed"] = installed
            self.save_catalog(catalog)
    
    def add_custom_server(self, server_info: Dict[str, Any]):
        """Add a custom server to the catalog"""
        catalog = self.load_catalog()
        server_name = server_info.get("name")
        
        if server_name:
            # Add default fields if missing
            server_info.setdefault("status", "custom")
            server_info.setdefault("installed", False)
            server_info.setdefault("running", False)
            server_info.setdefault("category", "custom")
            server_info.setdefault("tags", [])
            
            catalog["servers"][server_name] = server_info
            self.save_catalog(catalog)
            return True
        
        return False
    
    def remove_server(self, server_name: str):
        """Remove a server from the catalog"""
        catalog = self.load_catalog()
        if server_name in catalog.get("servers", {}):
            del catalog["servers"][server_name]
            self.save_catalog(catalog)
            return True
        return False
    
    def search_servers(self, query: str) -> Dict[str, Any]:
        """Search servers by name, description, or tags"""
        catalog = self.load_catalog()
        servers = catalog.get("servers", {})
        results = {}
        
        query_lower = query.lower()
        
        for name, server in servers.items():
            # Search in name
            if query_lower in name.lower():
                results[name] = server
                continue
            
            # Search in display name
            if query_lower in server.get("display_name", "").lower():
                results[name] = server
                continue
            
            # Search in description
            if query_lower in server.get("description", "").lower():
                results[name] = server
                continue
            
            # Search in tags
            tags = server.get("tags", [])
            if any(query_lower in tag.lower() for tag in tags):
                results[name] = server
                continue
        
        return results
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        catalog = self.load_catalog()
        categories = set(catalog.get("_metadata", {}).get("categories", []))
        
        # Add categories from servers
        for server in catalog.get("servers", {}).values():
            category = server.get("category")
            if category:
                categories.add(category)
        
        return sorted(list(categories))