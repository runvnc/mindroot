from typing import Dict, Set, Any
from lib.providers.services import service
from lib.providers.hooks import hook
from lib.service_registry import call_service

# Global event handlers dict
# Structure: { event_type: set(handler_services) }
_event_handlers: Dict[str, Set[str]] = {}

@hook()
async def startup(app, context=None):
    """Initialize the events system"""
    global _event_handlers
    _event_handlers = {}

@service()
async def subscribe(event_type: str, handler_service: str, context=None) -> bool:
    """Subscribe to an event type.
    
    Args:
        event_type: The type of event to subscribe to (e.g., 'usage.track')
        handler_service: Full service name (e.g., 'credits.handle_usage')
        
    Returns:
        bool: True if subscription was successful
    
    Example:
        await subscribe('usage.track', 'credits.handle_usage')
    """
    global _event_handlers
    
    if event_type not in _event_handlers:
        _event_handlers[event_type] = set()
    
    _event_handlers[event_type].add(handler_service)
    return True

@service()
async def publish(event_type: str, context=None, **event_data: Any) -> int:
    """Publish an event to all subscribers.
    
    Args:
        event_type: The type of event to publish
        context: The request context
        **event_data: Event data to pass to handlers
        
    Returns:
        int: Number of handlers notified
    
    Example:
        await publish('usage.track',
                    plugin_id='gpt4',
                    cost_type_id='tokens',
                    quantity=100)
    """
    if event_type not in _event_handlers:
        return 0
        
    count = 0
    for handler in _event_handlers[event_type]:
        await context[handler](context=context, **event_data)
        count += 1
        
    return count
