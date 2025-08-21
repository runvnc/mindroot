from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
import uuid
import json
from lib.providers.services import service
from lib.providers.commands import command
from lib.providers.hooks import hook
from lib.utils.debug import debug_box
from loguru import logger

from .models import SubscriptionPlan, UserSubscription, PlanFeature, PageTemplate
from .storage import SubscriptionStorage
from .subscription_manager import SubscriptionManager
from .credit_integration import CreditIntegration
from .default_templates import DEFAULT_HTML_TEMPLATE, DEFAULT_CSS_TEMPLATE, DEFAULT_JS_TEMPLATE

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
    storage, subscription_manager, credit_integration = plugin.create_components()
    
    # Store components globally
    global _subscription_manager, _credit_integration
    _subscription_manager = subscription_manager
    _credit_integration = credit_integration
    
    # Initialize default features if none exist
    features = await storage.get_all_features(active_only=False)
    if not features:
        await initialize_default_features(storage)
    
    # Initialize default template if none exist
    templates = await storage.get_all_templates()
    if not templates:
        await initialize_default_template(storage)
    
    debug_box("Subscriptions plugin initialized")

async def initialize_default_features(storage):
    """Initialize default plan features"""
    default_features = [
        {
            "feature_id": "sessions_per_month",
            "name": "Sessions Per Month",
            "description": "Number of sessions included per month",
            "type": "number",
            "default_value": 4,
            "display_order": 10
        },
        {
            "feature_id": "session_length",
            "name": "Session Length",
            "description": "Length of each session",
            "type": "select",
            "options": ["15 minutes", "30 minutes", "45 minutes", "60 minutes", "unlimited"],
            "default_value": "30 minutes",
            "display_order": 20
        },
        {
            "feature_id": "priority_support",
            "name": "Priority Support",
            "description": "Access to priority customer support",
            "type": "boolean",
            "default_value": False,
            "display_order": 30
        },
        {
            "feature_id": "additional_resources",
            "name": "Additional Resources",
            "description": "Access to additional resources and materials",
            "type": "boolean",
            "default_value": False,
            "display_order": 40
        }
    ]
    
    for feature_data in default_features:
        feature = PlanFeature.from_dict(feature_data)
        await storage.store_feature(feature)
        
    logger.info(f"Initialized {len(default_features)} default features")

async def initialize_default_template(storage):
    """Initialize default page template"""
    default_template = PageTemplate(
        template_id="default",
        name="Default Template",
        description="Standard subscription page template",
        html_template=DEFAULT_HTML_TEMPLATE,
        css_template=DEFAULT_CSS_TEMPLATE,
        js_template=DEFAULT_JS_TEMPLATE,
        is_default=True
    )
    
    await storage.store_template(default_template)
    logger.info("Initialized default page template")

# Plan management services

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
async def update_subscription_plan(plan_id: str, plan_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Update an existing subscription plan
    
    Args:
        plan_id: ID of the plan to update
        plan_data: Updated plan details
        context: Request context
    
    Returns:
        Dict: Updated plan details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    plan = await _subscription_manager.update_plan(plan_id, plan_data)
    return plan.to_dict()

@service()
async def deactivate_subscription_plan(plan_id: str, context=None) -> Dict[str, Any]:
    """Deactivate a subscription plan
    
    Args:
        plan_id: ID of the plan to deactivate
        context: Request context
    
    Returns:
        Dict: Status result
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    await _subscription_manager.deactivate_plan(plan_id)
    return {"status": "success", "message": f"Plan {plan_id} deactivated"}

@service()
async def activate_subscription_plan(plan_id: str, context=None) -> Dict[str, Any]:
    """Activate a subscription plan
    
    Args:
        plan_id: ID of the plan to activate
        context: Request context
    
    Returns:
        Dict: Status result
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    plan = await _subscription_manager.get_plan(plan_id)
    if not plan:
        return {"status": "error", "message": f"Plan {plan_id} not found"}
    
    plan.active = True
    await _subscription_manager.update_plan(plan_id, plan.to_dict())
    return {"status": "success", "message": f"Plan {plan_id} activated"}

# Feature management services

@service()
async def get_available_features(active_only: bool = True, context=None) -> List[Dict[str, Any]]:
    """Get all available plan features
    
    Args:
        active_only: Whether to return only active features
        context: Request context
    
    Returns:
        List[Dict]: List of feature details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    features = await _subscription_manager.storage.get_all_features(active_only)
    return [feature.to_dict() for feature in features]
@service()
async def create_plan_feature(feature_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Create a new plan feature
    
    Args:
        feature_data: Feature details
        context: Request context
    
    Returns:
        Dict: Created feature details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    # Generate feature ID if not provided
    if 'feature_id' not in feature_data:
        feature_data['feature_id'] = f"feature_{uuid.uuid4().hex[:8]}"
    
    feature = PlanFeature.from_dict(feature_data)
    await _subscription_manager.storage.store_feature(feature)
    
    return feature.to_dict()

@service()
async def update_plan_feature(feature_id: str, feature_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Update an existing plan feature
    
    Args:
        feature_id: ID of the feature to update
        feature_data: Updated feature details
        context: Request context
    
    Returns:
        Dict: Updated feature details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    feature = await _subscription_manager.storage.get_feature(feature_id)
    if not feature:
        return {"status": "error", "message": f"Feature {feature_id} not found"}
    
    # Update fields
    for key, value in feature_data.items():
        if hasattr(feature, key):
            setattr(feature, key, value)
    
    await _subscription_manager.storage.update_feature(feature)
    return feature.to_dict()

@service()
async def deactivate_plan_feature(feature_id: str, context=None) -> Dict[str, Any]:
    """Deactivate a plan feature
    
    Args:
        feature_id: ID of the feature to deactivate
        context: Request context
    
    Returns:
        Dict: Status result
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    feature = await _subscription_manager.storage.get_feature(feature_id)
    if not feature:
        return {"status": "error", "message": f"Feature {feature_id} not found"}
    
    feature.active = False
    await _subscription_manager.storage.update_feature(feature)
    return {"status": "success", "message": f"Feature {feature_id} deactivated"}

@service()
async def activate_plan_feature(feature_id: str, context=None) -> Dict[str, Any]:
    """Activate a plan feature
    
    Args:
        feature_id: ID of the feature to activate
        context: Request context
    
    Returns:
        Dict: Status result
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    feature = await _subscription_manager.storage.get_feature(feature_id)
    if not feature:
        return {"status": "error", "message": f"Feature {feature_id} not found"}
    
    feature.active = True
    await _subscription_manager.storage.update_feature(feature)
    return {"status": "success", "message": f"Feature {feature_id} activated"}

# Template management services

@service()
async def get_page_templates(context=None) -> List[Dict[str, Any]]:
    """Get all page templates
    
    Args:
        context: Request context
    
    Returns:
        List[Dict]: List of template details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    templates = await _subscription_manager.storage.get_all_templates()
    return [template.to_dict() for template in templates]

@service()
async def create_page_template(template_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Create a new page template
    
    Args:
        template_data: Template details
        context: Request context
    
    Returns:
        Dict: Created template details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    # Generate template ID if not provided
    if 'template_id' not in template_data:
        template_data['template_id'] = f"template_{uuid.uuid4().hex[:8]}"
    
    # Set is_default to False by default
    if 'is_default' not in template_data:
        template_data['is_default'] = False
    
    template = PageTemplate.from_dict(template_data)
    
    # If this is set as default, unset other defaults
    if template.is_default:
        await _subscription_manager.storage.set_default_template(template.template_id)
    
    await _subscription_manager.storage.store_template(template)
    return template.to_dict()

@service()
async def update_page_template(template_id: str, template_data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """Update an existing page template
    
    Args:
        template_id: ID of the template to update
        template_data: Updated template details
        context: Request context
    
    Returns:
        Dict: Updated template details
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    template = await _subscription_manager.storage.get_template(template_id)
    if not template:
        return {"status": "error", "message": f"Template {template_id} not found"}
    
    # Update fields
    for key, value in template_data.items():
        if hasattr(template, key):
            setattr(template, key, value)
    
    # If this is set as default, unset other defaults
    if template.is_default:
        await _subscription_manager.storage.set_default_template(template.template_id)
    
    await _subscription_manager.storage.store_template(template)
    return template.to_dict()

@service()
async def set_default_template(template_id: str, context=None) -> Dict[str, Any]:
    """Set a template as the default
    
    Args:
        template_id: ID of the template to set as default
        context: Request context
    
    Returns:
        Dict: Status result
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    success = await _subscription_manager.storage.set_default_template(template_id)
    
    if success:
        return {"status": "success", "message": f"Template {template_id} set as default"}
    else:
        return {"status": "error", "message": f"Template {template_id} not found"}

# Subscription event handling

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
            
            # Notify any plugins that handle subscription creation
            try:
                from lib.providers.services import service_manager
                await service_manager.handle_subscription_created(
                    user_id=username,
                    subscription_id=subscription.subscription_id,
                    plan_id=plan_id,
                    metadata=metadata
                )
                logger.info(f"Notified subscription handlers for {username}")
            except Exception as e:
                logger.error(f"Failed to notify subscription handlers: {e}")
            
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

# User subscription services

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

@service()
async def get_subscription_by_provider_id(provider_subscription_id: str, context=None) -> Optional[Dict]:
    """Get subscription by provider subscription ID (e.g., Stripe subscription ID)
    
    Args:
        provider_subscription_id: Provider's subscription ID
        context: Request context
    
    Returns:
        Optional[Dict]: Subscription details or None if not found
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    try:
        subscriptions = await _subscription_manager.get_subscriptions_by_provider_id(
            provider='stripe',
            provider_subscription_id=provider_subscription_id
        )
        return subscriptions[0].to_dict() if subscriptions else None
    except Exception as e:
        logger.error(f"Error getting subscription by provider ID: {e}")
        return None


@service()
async def update_subscription_status(subscription_id: str, status: str, context=None) -> Optional[Dict]:
    """Update a subscription's status
    
    Args:
        subscription_id: Internal subscription ID
        status: New status (active, canceled, etc.)
        context: Request context
    
    Returns:
        Optional[Dict]: Updated subscription details or None if not found
    """
    global _subscription_manager
    if not _subscription_manager:
        plugin = SubscriptionsPlugin(get_base_path(context))
        _, subscription_manager, _ = plugin.create_components()
        _subscription_manager = subscription_manager
    
    try:
        subscription = await _subscription_manager.update_subscription_status(subscription_id, status)
        return subscription.to_dict() if subscription else None
    except Exception as e:
        logger.error(f"Error updating subscription status: {e}")
        return None

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
