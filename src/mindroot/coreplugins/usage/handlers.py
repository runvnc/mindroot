from typing import Optional
from .models import UsageEvent
from .storage import UsageStorage
from loguru import logger
import traceback

class UsageTracker:
    def __init__(self, storage: UsageStorage):
        self.storage = storage

    async def get_cost(self, plugin_id: str, cost_type_id: str, model_id: Optional[str] = None) -> float:
        """Get the cost for a specific usage type and optional model"""
        costs = await self.storage.load_costs()
        try:

            plugin_costs = costs[plugin_id]
            type_costs = plugin_costs[cost_type_id]
            
            # Try model-specific cost first
            if model_id and 'model_specific' in type_costs:
                if model_id in type_costs['model_specific']:
                    return type_costs['model_specific'][model_id]
            
            # Fall back to default cost
            return type_costs.get('default', 0.0)
        except Exception as e:
            trace = traceback.format_exc()
            logger.error(f"Error getting cost: {e}\n\n{trace}")
            return 0.0

    async def track_usage(self, event: UsageEvent):
        """Track a usage event and store it with calculated cost"""
        unit_cost = await self.get_cost(event.plugin_id, event.cost_type_id, event.model_id)
        total_cost = unit_cost * event.quantity
        
        await self.storage.store_event(event, total_cost)

    async def get_usage(self, username: str, start_date=None, end_date=None):
        """Get usage records for a user"""
        return await self.storage.get_usage(username, start_date, end_date)

    async def get_total_cost(self, username: str, start_date=None, end_date=None):
        """Get total cost for a user"""
        return await self.storage.get_total_cost(username, start_date, end_date)
