from dataclasses import dataclass, field
from typing import Dict, Optional, Any, NamedTuple
from datetime import datetime
import uuid

class CostTypeInfo(NamedTuple):
    name: str
    description: str
    unit: str

@dataclass
class UsageEvent:
    timestamp: datetime
    plugin_id: str
    cost_type_id: str
    quantity: float
    metadata: Dict[str, Any]
    username: str
    model_id: Optional[str] = None  # e.g., 'gpt-4-1106-preview' or 'sd-xl-1.0'
    session_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'plugin_id': self.plugin_id,
            'cost_type_id': self.cost_type_id,
            'quantity': self.quantity,
            'metadata': self.metadata,
            'username': self.username,
            'model_id': self.model_id,
            'session_id': self.session_id,
            'request_id': self.request_id
        }

class CostTypeRegistry:
    def __init__(self):
        self._cost_types: Dict[str, CostTypeInfo] = {}

    def register(self, cost_type_id: str, description: str, unit: str) -> None:
        self._cost_types[cost_type_id] = CostTypeInfo(cost_type_id, description, unit)
    
    def get_info(self, cost_type_id: str) -> Optional[CostTypeInfo]:
        return self._cost_types.get(cost_type_id)
    
    def list_types(self) -> Dict[str, CostTypeInfo]:
        return self._cost_types.copy()

class CostConfig:
    def __init__(self):
        # Structure: {plugin_id: {cost_type_id: {model_id?: cost}}}
        self._costs: Dict[str, Dict[str, Dict[Optional[str], float]]] = {}
    
    def set_cost(self, plugin_id: str, cost_type_id: str, unit_cost: float, model_id: Optional[str] = None):
        if plugin_id not in self._costs:
            self._costs[plugin_id] = {}
        if cost_type_id not in self._costs[plugin_id]:
            self._costs[plugin_id][cost_type_id] = {}
        self._costs[plugin_id][cost_type_id][model_id] = unit_cost
    
    def get_cost(self, plugin_id: str, cost_type_id: str, model_id: Optional[str] = None) -> float:
        try:
            # Try to get model-specific cost first
            if model_id and model_id in self._costs[plugin_id][cost_type_id]:
                return self._costs[plugin_id][cost_type_id][model_id]
            # Fall back to default cost (None key)
            return self._costs[plugin_id][cost_type_id].get(None, 0.0)
        except KeyError:
            return 0.0
    
    def get_all_costs(self) -> Dict[str, Dict[str, Dict[Optional[str], float]]]:
        return self._costs.copy()
