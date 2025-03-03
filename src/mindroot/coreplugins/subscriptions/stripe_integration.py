from typing import Dict, Optional, Any
from decimal import Decimal
from loguru import logger
from .models import SubscriptionPlan

class StripeIntegration:
    """Handles integration with the Stripe payment plugin for subscription operations"""
    
    def __init__(self):
        pass
    
    async def create_checkout_session(self, username: str, plan: SubscriptionPlan) -> str:
        """Create a Stripe checkout session for subscription
        
        Args:
            username: User to create checkout for
            plan: Subscription plan details
            
        Returns:
            str: Checkout URL
        """
        try:
            # Import here to avoid circular imports
            from mr_stripe.mod import subscription_checkout, CheckoutUrls
            
            # Create checkout session
            checkout_url = await subscription_checkout(
                user_id=username,
                plan_name=plan.name,
                amount=Decimal(str(plan.price)),
                interval=plan.interval,
                currency=plan.currency,
                metadata={
                    'plan_id': plan.plan_id,
                    'credits_per_cycle': plan.credits_per_cycle,
                    'source': 'subscription_plugin'
                }
            )
            
            logger.info(f"Created Stripe checkout for {username}, plan: {plan.plan_id}")
            return checkout_url
            
        except Exception as e:
            logger.error(f"Failed to create Stripe checkout: {str(e)}")
            raise
    
    async def cancel_subscription(self, provider_subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel a Stripe subscription
        
        Args:
            provider_subscription_id: Stripe subscription ID
            at_period_end: Whether to cancel at period end or immediately
            
        Returns:
            bool: Success status
        """
        try:
            import stripe
            
            # Cancel subscription
            stripe.Subscription.modify(
                provider_subscription_id,
                cancel_at_period_end=at_period_end
            )
            
            logger.info(f"Cancelled Stripe subscription {provider_subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel Stripe subscription: {str(e)}")
            raise
