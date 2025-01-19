from datetime import datetime, date
from typing import Optional, Dict
from pathlib import Path
from lib.providers.services import service
from lib.providers.commands import command
from lib.providers.hooks import hook
from .models import UsageEvent
from .storage import UsageStorage
from .handlers import UsageTracker
from .reporting import UsageReport

# Initialize global instances
_storage = None
_tracker = None
_report = None

async def init_usage_tracking(base_path: str):
    """Initialize the usage tracking system"""
    global _storage, _tracker, _report
    
    _storage = UsageStorage(base_path)
    _tracker = UsageTracker(_storage)
    _report = UsageReport(_tracker)
    print("Usage tracking initialized")
    print("_tracker is ", _tracker)
    return (_tracker, _storage, _report)

@hook()
async def startup(app, context=None):
    # need to attach the tracker to the app
    _tracker, _storage, _report = await init_usage_tracking(str(Path.cwd()))
    app.state._tracker = _tracker
    app.state._storage = _storage
    app.state._report = _report
    await init_usage_tracking(str(Path.cwd()))


@service()
async def register_cost_type(plugin_id: str, cost_type_id: str, 
                           description: str, unit: str, context=None):
    """Register a new cost type for a plugin.
    
    Args:
        plugin_id: Unique identifier for the plugin
        cost_type_id: Unique identifier for the cost type (e.g., 'gpt4.input_tokens')
        description: Human-readable description of the cost type
        unit: Unit of measurement (e.g., 'tokens', 'images', 'api_calls')
        context: Request context
    
    Example:
        await register_cost_type(
            'gpt4',
            'gpt4.input_tokens',
            'GPT-4 input token cost',
            'tokens'
        )
    """
        
    _tracker.get_registry().register(cost_type_id, description, unit)

@service()
async def get_cost_types(context=None):
    """Get all registered cost types.
    
    Returns:
        Dict mapping cost_type_id to CostTypeInfo
    """
    return _tracker.get_registry().list_types()

@service()
async def track_usage(plugin_id: str, cost_type_id: str, quantity: float, 
                     metadata: dict, context=None, model_id: Optional[str] = None):
    """Track usage for a plugin.
    
    Args:
        plugin_id: Identifier for the plugin tracking usage
        cost_type_id: Type of cost being tracked
        quantity: Amount of usage in the specified unit
        metadata: Additional information about the usage
        context: Request context (must include username)
        model_id: Optional identifier for specific model used (e.g., 'gpt-4-1106-preview')
    
    Example:
        await track_usage(
            'gpt4',
            'gpt4.input_tokens',
            150,  # tokens
            {'prompt': 'Hello world'},
            model_id='gpt-4-1106-preview'
        )
    """
    if not context or not context.username:
        raise ValueError("Username required in context for usage tracking")

    if not _tracker.get_registry().get_info(cost_type_id):
        raise ValueError(f"Unknown cost type: {cost_type_id}")

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
    
    await _tracker.track_usage(event)

@service()
async def register_usage_handler(handler, context=None):
    """Register a new usage handler.
    
    This is an admin-only operation that allows adding new ways to handle
    usage events (e.g., for external billing systems).
    
    Args:
        handler: Instance of UsageHandler
        context: Request context (must have admin privileges)
    """
    _tracker.add_handler(handler)

@service()
async def get_cost_config(context=None):
    """Get the current cost configuration.
    
    Returns:
        CostConfig instance containing all configured costs
    """
    return _tracker.get_cost_config()

@service()
async def set_cost(plugin_id: str, cost_type_id: str, unit_cost: float, 
                  model_id: Optional[str] = None, context=None):
    """Set the cost for a specific usage type.
    
    This is an admin-only operation that configures the cost per unit
    for a specific type of usage.
    
    Args:
        plugin_id: Plugin identifier
        cost_type_id: Type of cost to configure
        unit_cost: Cost per unit
        model_id: Optional specific model identifier for model-specific pricing
        context: Request context (must have admin privileges)
    
    Example:
        # Set default cost for input tokens
        await set_cost('gpt4', 'gpt4.input_tokens', 0.0001)
        
        # Set model-specific cost
        await set_cost('gpt4', 'gpt4.input_tokens', 0.0003, 'gpt-4-1106-preview')
    """
    if not _tracker.get_registry().get_info(cost_type_id):
        raise ValueError(f"Unknown cost type: {cost_type_id}")
        
    if unit_cost < 0:
        raise ValueError("Cost per unit cannot be negative")
        
    _tracker.get_cost_config().set_cost(plugin_id, cost_type_id, unit_cost, model_id)

@command()
async def get_usage_report(username: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None, context=None) -> Dict:
    """Get a detailed usage report for a user.
    
    Args:
        username: The username to get report for
        start_date: Optional start date in ISO format (YYYY-MM-DD)
        end_date: Optional end date in ISO format (YYYY-MM-DD)
    
    Returns:
        Dict containing the usage report with:
        - Total costs
        - Usage broken down by plugin, cost type, and model
        - Individual usage events
    
    Example:
        report = await get_usage_report('user123', '2025-01-01', '2025-01-31')
    """
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    return await _report.get_user_report(username, start, end)

async def get_cost_summary(username: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None, context=None) -> Dict:
    """Get a cost summary for a user.
    
    Args:
        username: The username to get summary for
        start_date: Optional start date in ISO format (YYYY-MM-DD)
        end_date: Optional end date in ISO format (YYYY-MM-DD)
    
    Returns:
        Dict containing:
        - Total cost
        - Costs broken down by plugin and model
    
    Example:
        summary = await get_cost_summary('user123', '2025-01-01', '2025-01-31')
    """
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    return await _report.get_cost_summary(username, start, end)

async def get_daily_costs(username: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, context=None) -> Dict:
    """Get daily cost breakdown for a user.
    
    Args:
        username: The username to get daily costs for
        start_date: Optional start date in ISO format (YYYY-MM-DD)
        end_date: Optional end date in ISO format (YYYY-MM-DD)
    
    Returns:
        Dict containing costs broken down by day, plugin, and model
    
    Example:
        daily = await get_daily_costs('user123', '2025-01-01', '2025-01-31')
    """
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    
    return await _report.get_daily_costs(username, start, end)
