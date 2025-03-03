from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from lib.providers.services import service
from lib.providers.commands import command
from lib.providers.hooks import hook
from lib.utils.debug import debug_box
from loguru import logger

from .models import SubscriptionPlan, UserSubscription
from .storage import SubscriptionStorage
from .subscription_manager import SubscriptionManager
from .credit_integration import CreditIntegration

# Global components
_subscription_manager = None
_credit_integration = None

class SubscriptionsPlugin:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def create_components(self):
        """Create fresh instances of all subscription system components"""
        storage = SubscriptionStorage(self.base_path)
        subscription_manager = SubscriptionManager(storage, self.base_path)
        credit_integration = CreditIntegration()
        return storage, subscription_manager, credit_integration

def get_base_path(context) -> str:
    """Get the base path for subscription data storage"""
    return str(Path.cwd() / 'data' / 'subscriptions')

@hook()
async def startup(app, context=None):
    """Startup tasks"""
    # Initialize components
    plugin = SubscriptionsPlugin(get_base_path(context))
    _, subscription_manager, credit_integration = plugin.create_components()
    
    # Store components globally
    global _subscription_manager, _credit_integration
    _subscription_manager = subscription_manager
    _credit_integration = credit_integration
    
    debug_box("Subscriptions plugin initialized")

# Service methods

@service()
async def create_subscription_plan(plan_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Create a new subscription plan
    
    Args:
        plan_data: Plan details including name, description, price, etc.
        context: Request context
    
    Returns:
        Dict: Created plan details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    plan = await _subscription_manager.create_plan(plan_data)
    return plan.to_dict()

@service()
async def get_subscription_plans(active_only: bool = True, context=None) -> List[Dict[str, Any]]:
    """Get all subscription plans
    
    Args:
        active_only: Whether to return only active plans
        context: Request context
    
    Returns:
        List[Dict]: List of plan details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    plans = await _subscription_manager.list_plans(active_only)
    return [plan.to_dict() for plan in plans]

@service()
async def get_subscription_plan(plan_id: str, context=None) -> Optional[Dict[str, Any]]:
    """Get a subscription plan by ID
    
    Args:
        plan_id: ID of the plan to retrieve
        context: Request context
    
    Returns:
        Optional[Dict]: Plan details or None if not found
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    plan = await _subscription_manager.get_plan(plan_id)
    return plan.to_dict() if plan else None

@service()
async def process_subscription_event(event_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Process normalized subscription events from any payment provider
    
    Args:
        event_data: Normalized event data with provider, event type, etc.
        context: Request context
    
    Returns:
        Dict: Processing result
    """
    global _subscription_manager, _credit_integration
    if not _subscription_manager or not _credit_integration:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, credit_integration = plugin.create_components()
        _subscription_manager = subscription_manager
        _credit_integration = credit_integration
    
    provider = event_data.get('provider', 'unknown')
    normalized_event = event_data.get('normalized_event', {})
    event_type = normalized_event.get('event_type')
    
    logger.info(f"Processing {provider} subscription event: {event_type}")
    
    if event_type == 'subscription_created':
        # Extract data from normalized event
        username = normalized_event.get('username')
        metadata = normalized_event.get('metadata', {})
        plan_id = metadata.get('plan_id')
        provider_subscription_id = normalized_event.get('subscription_id')
        
        if not all([username, plan_id, provider_subscription_id]):
            logger.error(f"Missing required subscription data: username={username}, "
                        f"plan_id={plan_id}, subscription_id={provider_subscription_id}")
            return {'status': 'error', 'message': 'Missing required data'}
        
        # Create subscription record
        subscription = await _subscription_manager.create_subscription(
            username=username,
            plan_id=plan_id,
            provider_data={
                'provider': provider,
                'provider_subscription_id': provider_subscription_id
            }
        )
        
        # Allocate initial credits
        plan = await _subscription_manager.get_plan(plan_id)
        if plan:
            await _credit_integration.allocate_subscription_credits(
                username=username,
                amount=plan.credits_per_cycle,
                subscription_id=subscription.subscription_id,
                metadata={
                    'event': 'subscription_created',
                    'plan_id': plan_id,
                    'plan_name': plan.name,
                    'provider': provider
                }
            )
            
            return {
                'status': 'success',
                'event_type': event_type,
                'subscription_id': subscription.subscription_id,
                'credits_allocated': plan.credits_per_cycle
            }
        else:
            logger.error(f"Plan not found: {plan_id}")
            return {'status': 'error', 'message': f"Plan not found: {plan_id}"}
    
    elif event_type == 'subscription_renewed':
        # Handle subscription renewal
        provider_subscription_id = normalized_event.get('subscription_id')
        period_start = normalized_event.get('period_start')
        period_end = normalized_event.get('period_end')
        
        if not provider_subscription_id:
            logger.error("Missing subscription ID in renewal event")
            return {'status': 'error', 'message': 'Missing subscription ID'}
        
        # Find subscription by provider subscription ID
        subscriptions = await _subscription_manager.get_subscriptions_by_provider_id(
            provider=provider,
            provider_subscription_id=provider_subscription_id
        )
        
        if not subscriptions:
            logger.warning(f"No matching subscription found for renewal: {provider_subscription_id}")
            return {'status': 'error', 'message': 'Subscription not found'}
        
        subscription = subscriptions[0]
        
        # Update subscription period if provided
        if period_start and period_end:
            try:
                start_date = datetime.fromisoformat(period_start)
                end_date = datetime.fromisoformat(period_end)
                
                subscription = await _subscription_manager.update_subscription_period(
                    subscription_id=subscription.subscription_id,
                    period_start=start_date,
                    period_end=end_date
                )
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid date format in renewal event: {e}")
        
        # Allocate renewal credits
        plan = await _subscription_manager.get_plan(subscription.plan_id)
        if plan:
            await _credit_integration.allocate_subscription_credits(
                username=subscription.username,
                amount=plan.credits_per_cycle,
                subscription_id=subscription.subscription_id,
                metadata={
                    'event': 'subscription_renewed',
                    'plan_id': plan.plan_id,
                    'plan_name': plan.name,
                    'provider': provider,
                    'invoice_id': normalized_event.get('invoice_id')
                }
            )
            
            return {
                'status': 'success',
                'event_type': event_type,
                'subscription_id': subscription.subscription_id,
                'credits_allocated': plan.credits_per_cycle
            }
        else:
            logger.error(f"Plan not found for renewal: {subscription.plan_id}")
            return {'status': 'error', 'message': f"Plan not found: {subscription.plan_id}"}
    
    elif event_type == 'subscription_updated':
        # Handle subscription updates
        provider_subscription_id = normalized_event.get('subscription_id')
        status = normalized_event.get('status')
        cancel_at_period_end = normalized_event.get('cancel_at_period_end')
        
        if not provider_subscription_id:
            logger.error("Missing subscription ID in update event")
            return {'status': 'error', 'message': 'Missing subscription ID'}
        
        # Find subscription by provider subscription ID
        subscriptions = await _subscription_manager.get_subscriptions_by_provider_id(
            provider=provider,
            provider_subscription_id=provider_subscription_id
        )
        
        if not subscriptions:
            logger.warning(f"No matching subscription found for update: {provider_subscription_id}")
            return {'status': 'error', 'message': 'Subscription not found'}
        
        subscription = subscriptions[0]
        
        # Update subscription status if provided
        if status:
            subscription = await _subscription_manager.update_subscription_status(
                subscription_id=subscription.subscription_id,
                status=status
            )
        
        # Update cancel_at_period_end if provided
        if cancel_at_period_end is not None:
            subscription.cancel_at_period_end = cancel_at_period_end
            await _subscription_manager.update_subscription(subscription)
        
        return {
            'status': 'success',
            'event_type': event_type,
            'subscription_id': subscription.subscription_id
        }
    
    elif event_type == 'subscription_canceled':
        # Handle subscription cancellation
        provider_subscription_id = normalized_event.get('subscription_id')
        
        if not provider_subscription_id:
            logger.error("Missing subscription ID in cancellation event")
            return {'status': 'error', 'message': 'Missing subscription ID'}
        
        # Find subscription by provider subscription ID
        subscriptions = await _subscription_manager.get_subscriptions_by_provider_id(
            provider=provider,
            provider_subscription_id=provider_subscription_id
        )
        
        if not subscriptions:
            logger.warning(f"No matching subscription found for cancellation: {provider_subscription_id}")
            return {'status': 'error', 'message': 'Subscription not found'}
        
        subscription = subscriptions[0]
        
        # Update subscription status to canceled
        subscription = await _subscription_manager.update_subscription_status(
            subscription_id=subscription.subscription_id,
            status='canceled'
        )
        
        return {
            'status': 'success',
            'event_type': event_type,
            'subscription_id': subscription.subscription_id
        }
    
    # Unknown event type
    logger.warning(f"Unknown subscription event type: {event_type}")
    return {'status': 'ignored', 'event_type': event_type}

@service()
async def get_user_subscriptions(username: str, context=None) -> List[Dict[str, Any]]:
    """Get all subscriptions for a user
    
    Args:
        username: User to get subscriptions for
        context: Request context
    
    Returns:
        List[Dict]: List of subscription details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    subscriptions = await _subscription_manager.get_user_subscriptions(username)
    return [sub.to_dict() for sub in subscriptions]

@service()
async def cancel_subscription(subscription_id: str, at_period_end: bool = True, context=None) -> Dict[str, Any]:
    """Cancel a user subscription
    
    Args:
        subscription_id: ID of the subscription to cancel
        at_period_end: Whether to cancel at period end or immediately
        context: Request context
    
    Returns:
        Dict: Updated subscription details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    # Get subscription details
    subscription = await _subscription_manager.get_subscription(subscription_id)
    if not subscription:
        raise ValueError(f"Subscription not found: {subscription_id}")
    
    # Cancel with payment provider if applicable
    if subscription.provider_subscription_id:
        from lib.providers.services import service_manager
        
        try:
            # Call provider-specific cancellation service if available
            # The service name follows the pattern: cancel_{provider}_subscription
            cancel_service = f"cancel_{subscription.payment_provider}_subscription"
            if hasattr(service_manager, cancel_service):
                await getattr(service_manager, cancel_service)(
                    provider_subscription_id=subscription.provider_subscription_id,
                    at_period_end=at_period_end
                )
        except Exception as e:
            logger.error(f"Failed to cancel with provider: {e}")
            # Continue with local cancellation even if provider fails
    
    # Update subscription status
    updated_subscription = await _subscription_manager.cancel_subscription(
        subscription_id, 
        at_period_end
    )
    
    return updated_subscription.to_dict()

# Command methods

@command()
async def list_subscription_plans(params, context=None):
    """List available subscription plans
    
    Example:
        { "list_subscription_plans": {} }
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    plans = await _subscription_manager.list_plans(active_only=True)
    
    if not plans:
        return "No subscription plans are currently available."
    
    result = "Available Subscription Plans:\n\n"
    
    for plan in plans:
        result += f"Plan: {plan.name}\n"
        result += f"Description: {plan.description}\n"
        result += f"Price: {plan.price} {plan.currency}/{plan.interval}\n"
        result += f"Credits: {plan.credits_per_cycle} per {plan.interval}\n"
        
        if plan.features:
            result += "Features:\n"
            for feature, value in plan.features.items():
                result += f"- {feature}: {value}\n"
        
        result += "\n"
    
    return result

@command()
async def get_my_subscriptions(params, context=None):
    """Get current user's subscriptions
    
    Example:
        { "get_my_subscriptions": {} }
    """
    if not context or not context.username:
        return "You must be logged in to view your subscriptions."
    
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    subscriptions = await _subscription_manager.get_user_subscriptions(context.username)
    
    if not subscriptions:
        return "You don't have any active subscriptions."
    
    result = "Your Subscriptions:\n\n"
    
    for sub in subscriptions:
        plan = await _subscription_manager.get_plan(sub.plan_id)
        plan_name = plan.name if plan else "Unknown Plan"
        
        result += f"Plan: {plan_name}\n"
        result += f"Status: {sub.status}\n"
        result += f"Current period: {sub.current_period_start.strftime('%Y-%m-%d')} to {sub.current_period_end.strftime('%Y-%m-%d')}\n"
        
        if sub.cancel_at_period_end:
            result += "Will cancel at end of current period\n"
        
        result += "\n"
    
    return result
