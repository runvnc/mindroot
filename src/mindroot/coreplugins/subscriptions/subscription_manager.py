from datetime import datetime
from typing import Dict, Optional, List, Any
import uuid
from .models import SubscriptionPlan, UserSubscription
from .storage import SubscriptionStorage

class SubscriptionManager:
    def __init__(self, storage: SubscriptionStorage, base_path: str):
        self.storage = storage
        self.base_path = base_path
    
    # Plan management methods
    
    async def create_plan(self, plan_data: Dict[str, Any]) -> SubscriptionPlan:
        """Create a new subscription plan"""
        # Generate a plan ID if not provided
        if 'plan_id' not in plan_data:
            plan_data['plan_id'] = f"plan_{uuid.uuid4().hex[:8]}"
        
        # Validate required fields
        required_fields = ['name', 'description', 'price', 'credits_per_cycle']
        for field in required_fields:
            if field not in plan_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create plan object
        plan = SubscriptionPlan.from_dict(plan_data)
        
        # Store plan
        await self.storage.store_plan(plan)
        
        return plan
    
    async def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by ID"""
        return await self.storage.get_plan(plan_id)
    
    async def list_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        """List all subscription plans"""
        return await self.storage.get_all_plans(active_only)
    
    async def update_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> SubscriptionPlan:
        """Update an existing subscription plan"""
        existing_plan = await self.storage.get_plan(plan_id)
        
        if not existing_plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        # Update fields
        for key, value in plan_data.items():
            if hasattr(existing_plan, key):
                setattr(existing_plan, key, value)
        
        # Store updated plan
        await self.storage.update_plan(existing_plan)
        
        return existing_plan
    
    async def deactivate_plan(self, plan_id: str) -> None:
        """Deactivate a subscription plan"""
        existing_plan = await self.storage.get_plan(plan_id)
        
        if not existing_plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        existing_plan.active = False
        await self.storage.update_plan(existing_plan)
    
    # Subscription management methods
    
    async def create_subscription(self, username: str, plan_id: str, provider_data: Dict[str, Any]) -> UserSubscription:
        """Create a new user subscription"""
        plan = await self.storage.get_plan(plan_id)
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        if not plan.active:
            raise ValueError(f"Plan is not active: {plan_id}")
        
        # Create subscription object
        now = datetime.now()
        subscription = UserSubscription(
            subscription_id=f"sub_{uuid.uuid4().hex[:8]}",
            username=username,
            plan_id=plan_id,
            status='active',
            current_period_start=now,
            current_period_end=now,  # Will be updated with provider data
            payment_provider=provider_data.get('provider', 'stripe'),
            provider_subscription_id=provider_data.get('provider_subscription_id'),
            metadata={
                'plan_name': plan.name,
                'plan_price': plan.price,
                'plan_currency': plan.currency,
                'plan_interval': plan.interval,
                'credits_per_cycle': plan.credits_per_cycle
            }
        )
        
        # Store subscription
        await self.storage.store_subscription(subscription)
        
        return subscription
    
    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> UserSubscription:
        """Cancel a user subscription"""
        subscription = await self.storage.get_subscription(subscription_id)
        
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        if at_period_end:
            subscription.cancel_at_period_end = True
        else:
            subscription.status = 'canceled'
        
        await self.storage.update_subscription(subscription)
        
        return subscription
    
    async def update_subscription_status(self, subscription_id: str, status: str) -> UserSubscription:
        """Update a subscription's status"""
        subscription = await self.storage.get_subscription(subscription_id)
        
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        subscription.status = status
        await self.storage.update_subscription(subscription)
        
        return subscription
    
    async def get_user_subscriptions(self, username: str) -> List[UserSubscription]:
        """Get all subscriptions for a user"""
        return await self.storage.get_user_subscriptions(username)

    async def get_subscriptions_by_provider_id(self, provider: str, provider_subscription_id: str) -> List[UserSubscription]:
        """Get subscriptions by provider subscription ID"""
        return await self.storage.get_subscriptions_by_provider_id(provider, provider_subscription_id)
    
    async def update_subscription_period(self, subscription_id: str, 
                                       period_start: datetime, 
                                       period_end: datetime) -> UserSubscription:
        """Update a subscription's billing period"""
        subscription = await self.storage.get_subscription(subscription_id)
        
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        subscription.current_period_start = period_start
        subscription.current_period_end = period_end
        await self.storage.update_subscription(subscription)
        
        return subscription
