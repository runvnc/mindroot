from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Optional, Iterator
import os
from .models import SubscriptionPlan, UserSubscription

class SubscriptionStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.plans_dir = self.base_path / 'plans'
        self.subscriptions_dir = self.base_path / 'subscriptions'
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.subscriptions_dir.mkdir(parents=True, exist_ok=True)
    
    # Plan management methods
    
    async def store_plan(self, plan: SubscriptionPlan) -> None:
        """Store a subscription plan"""
        plan_file = self.plans_dir / f"{plan.plan_id}.json"
        
        with open(plan_file, 'w') as f:
            json.dump(plan.to_dict(), f, indent=2)
    
    async def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by ID"""
        plan_file = self.plans_dir / f"{plan_id}.json"
        
        if not plan_file.exists():
            return None
        
        try:
            with open(plan_file, 'r') as f:
                data = json.load(f)
                return SubscriptionPlan.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    async def get_all_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        """Get all subscription plans"""
        plans = []
        
        for plan_file in self.plans_dir.glob('*.json'):
            try:
                with open(plan_file, 'r') as f:
                    data = json.load(f)
                    plan = SubscriptionPlan.from_dict(data)
                    
                    if active_only and not plan.active:
                        continue
                        
                    plans.append(plan)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return sorted(plans, key=lambda p: p.price)
    
    async def update_plan(self, plan: SubscriptionPlan) -> None:
        """Update a subscription plan"""
        await self.store_plan(plan)
    
    # Subscription management methods
    
    async def store_subscription(self, subscription: UserSubscription) -> None:
        """Store a user subscription"""
        user_dir = self.subscriptions_dir / subscription.username
        user_dir.mkdir(parents=True, exist_ok=True)
        
        subscription_file = user_dir / f"{subscription.subscription_id}.json"
        
        with open(subscription_file, 'w') as f:
            json.dump(subscription.to_dict(), f, indent=2)
    
    async def get_subscription(self, subscription_id: str) -> Optional[UserSubscription]:
        """Get a subscription by ID"""
        # We need to search all user directories
        for user_dir in self.subscriptions_dir.iterdir():
            if not user_dir.is_dir():
                continue
                
            subscription_file = user_dir / f"{subscription_id}.json"
            
            if subscription_file.exists():
                try:
                    with open(subscription_file, 'r') as f:
                        data = json.load(f)
                        return UserSubscription.from_dict(data)
                except (json.JSONDecodeError, KeyError):
                    return None
        
        return None
    
    async def get_user_subscriptions(self, username: str) -> List[UserSubscription]:
        """Get all subscriptions for a user"""
        user_dir = self.subscriptions_dir / username
        
        if not user_dir.exists():
            return []
        
        subscriptions = []
        
        for subscription_file in user_dir.glob('*.json'):
            try:
                with open(subscription_file, 'r') as f:
                    data = json.load(f)
                    subscription = UserSubscription.from_dict(data)
                    subscriptions.append(subscription)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return sorted(subscriptions, key=lambda s: s.created_at, reverse=True)
    
    async def update_subscription(self, subscription: UserSubscription) -> None:
        """Update a user subscription"""
        subscription.updated_at = datetime.now()
        await self.store_subscription(subscription)
    
    async def get_subscriptions_by_provider_id(self, provider: str, provider_subscription_id: str) -> List[UserSubscription]:
        """Get subscriptions by provider subscription ID"""
        result = []
        
        # Search all user directories
        for user_dir in self.subscriptions_dir.iterdir():
            if not user_dir.is_dir():
                continue
                
            for subscription_file in user_dir.glob('*.json'):
                try:
                    with open(subscription_file, 'r') as f:
                        data = json.load(f)
                        
                        if (data.get('payment_provider') == provider and 
                            data.get('provider_subscription_id') == provider_subscription_id):
                            subscription = UserSubscription.from_dict(data)
                            result.append(subscription)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return result
