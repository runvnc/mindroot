from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path
import json
import uuid

@dataclass
class CreditTransaction:
    timestamp: datetime
    username: str
    amount: float      # Positive for allocations, negative for usage
    balance: float     # Running balance after this transaction
    type: str         # 'allocation', 'usage', 'refund', 'expiration'
    source: str       # 'purchase', 'admin_grant', 'usage_deduction', etc.
    reference_id: str  # Links to usage event or purchase/admin action
    metadata: Dict[str, Any] = field(default_factory=dict)
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'username': self.username,
            'amount': self.amount,
            'balance': self.balance,
            'type': self.type,
            'source': self.source,
            'reference_id': self.reference_id,
            'metadata': self.metadata,
            'transaction_id': self.transaction_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CreditTransaction':
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class CreditRatioConfig:
    """Manages the hierarchical credit ratio configuration"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path) / 'config'
        self.config_file = self.base_path / 'ratio_config.json'
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default config if file doesn't exist or is invalid
            return {
                'default_ratio': 100.0,  # 1 cent = 100 credits by default
                'plugins': {}
            }
    
    async def _save_config(self, config: Dict) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    async def set_ratio(self, ratio: float, plugin_id: Optional[str] = None,
                       cost_type_id: Optional[str] = None,
                       model_id: Optional[str] = None) -> None:
        """Set a credit ratio at the specified level"""
        if ratio <= 0:
            raise ValueError("Ratio must be positive")
            
        config = await self._load_config()
            
        if not plugin_id:
            config['default_ratio'] = ratio
            await self._save_config(config)
            return
            
        if plugin_id not in config['plugins']:
            config['plugins'][plugin_id] = {
                'default_ratio': None,
                'cost_types': {},
                'models': {}
            }
        
        plugin_config = config['plugins'][plugin_id]
        
        if model_id:
            if model_id not in plugin_config['models']:
                plugin_config['models'][model_id] = {
                    'default_ratio': None,
                    'cost_types': {}
                }
            
            if cost_type_id:
                plugin_config['models'][model_id]['cost_types'][cost_type_id] = ratio
            else:
                plugin_config['models'][model_id]['default_ratio'] = ratio
        elif cost_type_id:
            plugin_config['cost_types'][cost_type_id] = ratio
        else:
            plugin_config['default_ratio'] = ratio
            
        await self._save_config(config)
    
    async def get_ratio(self, plugin_id: str, cost_type_id: str,
                       model_id: Optional[str] = None) -> float:
        """Get the appropriate credit ratio following the resolution order"""
        config = await self._load_config()
        plugin_config = config['plugins'].get(plugin_id, {})
        
        # 1. Check model-specific cost type ratio
        if model_id and model_id in plugin_config.get('models', {}):
            model_config = plugin_config['models'][model_id]
            if cost_type_id in model_config.get('cost_types', {}):
                return model_config['cost_types'][cost_type_id]
            
            # 2. Check model default ratio
            if model_config.get('default_ratio') is not None:
                return model_config['default_ratio']
        
        # 3. Check plugin cost type ratio
        if cost_type_id in plugin_config.get('cost_types', {}):
            return plugin_config['cost_types'][cost_type_id]
        
        # 4. Check plugin default ratio
        if plugin_config.get('default_ratio') is not None:
            return plugin_config['default_ratio']
        
        # 5. Use global default ratio
        return config['default_ratio']
    
    async def get_config(self) -> Dict:
        """Get the full configuration"""
        return await self._load_config()
    
    async def set_config(self, config: Dict) -> None:
        """Set the full configuration"""
        # Basic validation
        if 'default_ratio' not in config:
            raise ValueError("Configuration must include default_ratio")
        if config['default_ratio'] <= 0:
            raise ValueError("Default ratio must be positive")
            
        await self._save_config(config)
