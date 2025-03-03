from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime
import uuid

@dataclass
class SubscriptionPlan:
    plan_id: str
    name: str
    description: str
    price: float
    currency: str = 'USD'
    interval: str = 'month'  # 'month' or 'year'
    credits_per_cycle: float
    features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    
    def to_dict(self) -> dict:
        return {
            'plan_id': self.plan_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'currency': self.currency,
            'interval': self.interval,
            'credits_per_cycle': self.credits_per_cycle,
            'features': self.features,
            'metadata': self.metadata,
            'active': self.active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SubscriptionPlan':
        return cls(**data)

@dataclass
class UserSubscription:
    subscription_id: str
    username: str
    plan_id: str
    status: str  # 'active', 'canceled', 'past_due', 'trialing'
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    payment_provider: str = 'stripe'
    provider_subscription_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'subscription_id': self.subscription_id,
            'username': self.username,
            'plan_id': self.plan_id,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'cancel_at_period_end': self.cancel_at_period_end,
            'payment_provider': self.payment_provider,
            'provider_subscription_id': self.provider_subscription_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSubscription':
        data = data.copy()
        data['current_period_start'] = datetime.fromisoformat(data['current_period_start'])
        data['current_period_end'] = datetime.fromisoformat(data['current_period_end'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
