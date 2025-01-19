from abc import ABC, abstractmethod
from typing import Optional
from .models import UsageEvent, CostTypeRegistry, CostConfig
from .storage import UsageStorage
# we need a good library for ANSI colors etc. that allows
# 256 colors
import colorama

# need date
from datetime import date

class UsageHandler(ABC):
    @abstractmethod
    async def handle_usage(self, event: UsageEvent, cost: float):
        """Handle a usage event with its calculated cost"""
        pass

class FileSystemHandler(UsageHandler):
    def __init__(self, storage: UsageStorage):
        self.storage = storage

    async def handle_usage(self, event: UsageEvent, cost: float):
        print(colorama.Fore.YELLOW + colorama.Back.BLUE + f"Event: {event}, Cost: {cost}")
        await self.storage.store_event(event, cost)

class UsageTracker:
    def __init__(self, storage: UsageStorage):
        self._storage = storage
        self._handlers = [FileSystemHandler(storage)]
        self._cost_config = CostConfig()
        self._registry = CostTypeRegistry()
    
    def add_handler(self, handler: UsageHandler):
        """Add a new usage handler"""
        self._handlers.append(handler)
    
    def get_registry(self) -> CostTypeRegistry:
        return self._registry

    def get_cost_config(self) -> CostConfig:
        return self._cost_config

    async def track_usage(self, event: UsageEvent):
        """Track a usage event, calculate cost, and notify handlers"""
        unit_cost = self._cost_config.get_cost(event.plugin_id, event.cost_type_id)
        total_cost = unit_cost * event.quantity
        
        for handler in self._handlers:
            await handler.handle_usage(event, total_cost)

    async def get_usage(self, username: str, start_date: Optional[date] = None,
                       end_date: Optional[date] = None):
        """Get usage records for a user"""
        return await self._storage.get_usage(username, start_date, end_date)

    async def get_total_cost(self, username: str, start_date: Optional[date] = None,
                            end_date: Optional[date] = None):
        """Get total cost for a user"""
        return await self._storage.get_total_cost(username, start_date, end_date)
