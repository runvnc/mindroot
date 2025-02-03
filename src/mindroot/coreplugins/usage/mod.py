from datetime import datetime, date
from typing import Optional, Dict
from pathlib import Path
from lib.providers.services import service
from lib.providers.commands import command
from .models import UsageEvent
from .storage import UsageStorage
from .handlers import UsageTracker
from .reporting import UsageReport
from lib.providers.hooks import hook, hook_manager

def get_base_path() -> str:
    return str(Path.cwd())

@service()
async def register_cost_type(plugin_id: str, cost_type_id: str, 
                           description: str, unit: str, context=None):
    """Register a new cost type for a plugin."""
    storage = UsageStorage(get_base_path())
    await storage.save_cost_type(cost_type_id, {
        "name": cost_type_id,
        "description": description,
        "unit": unit
    })

@service()
async def get_cost_types(context=None):
    """Get all registered cost types."""
    storage = UsageStorage(get_base_path())
    return await storage.load_cost_types()

@service()
async def track_usage(plugin_id: str, cost_type_id: str, quantity: float, 
                     metadata: dict, context=None, model_id: Optional[str] = None):
    """Track usage for a plugin."""
    if not context or not context.username:
        raise ValueError("Username required in context for usage tracking")

    storage = UsageStorage(get_base_path())
    tracker = UsageTracker(storage)

    event = UsageEvent(
        timestamp=datetime.now(),
        plugin_id=plugin_id,
        cost_type_id=cost_type_id,
        quantity=quantity,
        metadata=metadata,
        username=context.username,
        model_id=model_id,
        session_id=context.log_id
    )
    
    await tracker.track_usage(event)
    
    # Publish usage event for other plugins (like credits) to handle
    await hook_manager.handle_usage(
                  plugin_id=plugin_id,
                  cost_type_id=cost_type_id,
                  quantity=quantity,
                  metadata=metadata,
                  context=context,
                  model_id=model_id)

@service()
async def set_cost(plugin_id: str, cost_type_id: str, unit_cost: float, 
                  model_id: Optional[str] = None, context=None):
    """Set the cost for a specific usage type."""
    if unit_cost < 0:
        raise ValueError("Cost per unit cannot be negative")

    storage = UsageStorage(get_base_path())
    cost_types = await storage.load_cost_types()
    
    if cost_type_id not in cost_types:
        raise ValueError(f"Unknown cost type: {cost_type_id}")
        
    await storage.save_cost(plugin_id, cost_type_id, unit_cost, model_id)

@command()
async def get_usage_report(username: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None, context=None) -> Dict:
    """Get a detailed usage report for a user."""
    storage = UsageStorage(get_base_path())
    report = UsageReport(storage)
    
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    return await report.get_user_report(username, start, end)

@command()
async def get_cost_summary(username: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None, context=None) -> Dict:
    """Get a cost summary for a user."""
    storage = UsageStorage(get_base_path())
    report = UsageReport(storage)
    
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    return await report.get_cost_summary(username, start, end)

@command()
async def get_daily_costs(username: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, context=None) -> Dict:
    """Get daily cost breakdown for a user."""
    storage = UsageStorage(get_base_path())
    report = UsageReport(storage)
    
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    return await report.get_daily_costs(username, start, end)

@service()
async def get_cost(plugin_id: str, cost_type_id: str, model_id: Optional[str] = None, context=None) -> float:
    storage = UsageStorage(get_base_path())
    costs = await storage.load_costs()
    try:
        plugin_costs = costs[plugin_id][cost_type_id]
        # Use model-specific cost if provided
        if model_id and 'model_specific' in plugin_costs and model_id in plugin_costs['model_specific']:
            return plugin_costs['model_specific'][model_id]
        # Otherwise, return the default cost
        return plugin_costs['default']
    except KeyError:
        raise ValueError(f"No cost set for plugin {plugin_id} with cost type {cost_type_id}")

