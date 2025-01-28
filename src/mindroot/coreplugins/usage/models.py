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
