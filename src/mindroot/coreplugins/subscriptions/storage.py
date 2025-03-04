from pathlib import Path
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Iterator
import os
from .models import SubscriptionPlan, UserSubscription, PlanFeature, PageTemplate

class SubscriptionStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.plans_dir = self.base_path / 'plans'
        self.subscriptions_dir = self.base_path / 'subscriptions'
        self.features_dir = self.base_path / 'features'
        self.templates_dir = self.base_path / 'templates'
        
        # Create directories if they don't exist
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.subscriptions_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    # Feature management methods
    
    async def store_feature(self, feature: PlanFeature) -> None:
        """Store a plan feature"""
        feature_file = self.features_dir / f"{feature.feature_id}.json"
        
        with open(feature_file, 'w') as f:
            json.dump(feature.to_dict(), f, indent=2)
    
    async def get_feature(self, feature_id: str) -> Optional[PlanFeature]:
        """Get a plan feature by ID"""
        feature_file = self.features_dir / f"{feature_id}.json"
        
        if not feature_file.exists():
            return None
        
        try:
            with open(feature_file, 'r') as f:
                data = json.load(f)
                return PlanFeature.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    async def get_all_features(self, active_only: bool = True) -> List[PlanFeature]:
        """Get all plan features"""
        features = []
        
        for feature_file in self.features_dir.glob('*.json'):
            try:
                with open(feature_file, 'r') as f:
                    data = json.load(f)
                    feature = PlanFeature.from_dict(data)
                    
                    if active_only and not feature.active:
                        continue
                        
                    features.append(feature)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return sorted(features, key=lambda f: f.display_order)
    
    async def update_feature(self, feature: PlanFeature) -> None:
        """Update a plan feature"""
        await self.store_feature(feature)
    
    # Template management methods
    
    async def store_template(self, template: PageTemplate) -> None:
        """Store a page template"""
        template_file = self.templates_dir / f"{template.template_id}.json"
        
        with open(template_file, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
    
    async def get_template(self, template_id: str) -> Optional[PageTemplate]:
        """Get a page template by ID"""
        template_file = self.templates_dir / f"{template_id}.json"
        
        if not template_file.exists():
            return None
        
        try:
            with open(template_file, 'r') as f:
                data = json.load(f)
                return PageTemplate.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    async def get_all_templates(self) -> List[PageTemplate]:
        """Get all page templates"""
        templates = []
        
        for template_file in self.templates_dir.glob('*.json'):
            try:
                with open(template_file, 'r') as f:
                    data = json.load(f)
                    template = PageTemplate.from_dict(data)
                    templates.append(template)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return templates
    
    async def get_default_template(self) -> Optional[PageTemplate]:
        """Get the default page template"""
        templates = await self.get_all_templates()
        
        for template in templates:
            if template.is_default:
                return template
        
        return templates[0] if templates else None
    
    async def set_default_template(self, template_id: str) -> bool:
        """Set a template as the default"""
        templates = await self.get_all_templates()
        
        # First, unset default on all templates
        for template in templates:
            if template.is_default:
                template.is_default = False
                await self.store_template(template)
        
        # Then set the new default
        template = await self.get_template(template_id)
        if template:
            template.is_default = True
            await self.store_template(template)
            return True
        
        return False
