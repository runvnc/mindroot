from typing import Dict, Optional, Any
from datetime import datetime
from loguru import logger
from .subscription_manager import SubscriptionManager
from .credit_integration import CreditIntegration

class WebhookHandler:
    """Handles webhook events from payment providers for subscription events"""
    
    def __init__(self, subscription_manager: SubscriptionManager, credit_integration: CreditIntegration):
        self.subscription_manager = subscription_manager
        self.credit_integration = credit_integration
        self.processed_events = set()  # For idempotency
    
    async def handle_stripe_event(self, event: Dict[str, Any]) -> Optional[Dict]:
        """Process Stripe webhook events related to subscriptions
        
        Args:
            event: Stripe event object
            
        Returns:
            Optional[Dict]: Processing result
        """
        event_id = event.get('id')
        event_type = event.get('type')
        
        logger.info(f"Processing Stripe event: {event_type} ({event_id})")
        
        # Ensure idempotency
        if event_id in self.processed_events:
            logger.info(f"Event already processed: {event_id}")
            return {'status': 'already_processed', 'event_id': event_id}
        
        try:
            if event_type == 'checkout.session.completed':
                await self._handle_checkout_completed(event)
            elif event_type == 'invoice.paid':
                await self._handle_invoice_paid(event)
            elif event_type == 'customer.subscription.updated':
                await self._handle_subscription_updated(event)
            elif event_type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event)
            else:
                logger.info(f"Ignoring unhandled event type: {event_type}")
                return {'status': 'ignored', 'event_id': event_id, 'event_type': event_type}
            
            # Mark as processed
            self.processed_events.add(event_id)
            return {'status': 'success', 'event_id': event_id, 'event_type': event_type}
        
        except Exception as e:
            logger.error(f"Error processing event {event_id}: {str(e)}")
            return {'status': 'error', 'event_id': event_id, 'error': str(e)}
    
    async def _handle_checkout_completed(self, event: Dict[str, Any]) -> None:
        """Handle initial subscription creation and credit allocation"""
        session = event['data']['object']
        
        # Only process subscription checkouts
        if session.get('mode') != 'subscription':
            logger.info(f"Ignoring non-subscription checkout: {session.get('id')}")
            return
        
        username = session.get('client_reference_id')
        subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})
        plan_id = metadata.get('plan_id')
        
        if not all([username, subscription_id, plan_id]):
            logger.error(f"Missing required subscription data: username={username}, "
                        f"subscription_id={subscription_id}, plan_id={plan_id}")
            raise ValueError("Missing required subscription data")
        
        logger.info(f"Creating subscription for {username}, plan: {plan_id}")
        
        # Create subscription record
        subscription = await self.subscription_manager.create_subscription(
            username=username,
            plan_id=plan_id,
            provider_data={
                'provider': 'stripe',
                'provider_subscription_id': subscription_id
            }
        )
        
        # Allocate initial credits
        plan = await self.subscription_manager.get_plan(plan_id)
        if plan:
            logger.info(f"Allocating {plan.credits_per_cycle} credits to {username}")
            await self.credit_integration.allocate_subscription_credits(
                username=username,
                amount=plan.credits_per_cycle,
                subscription_id=subscription.subscription_id,
                metadata={
                    'event': 'subscription_created',
                    'plan_id': plan_id,
                    'plan_name': plan.name,
                    'stripe_session_id': session.get('id')
                }
            )
        else:
            logger.error(f"Plan not found: {plan_id}")
    
    async def _handle_invoice_paid(self, event: Dict[str, Any]) -> None:
        """Handle subscription renewal and credit allocation"""
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            logger.info(f"Invoice has no subscription: {invoice.get('id')}")
            return
        
        logger.info(f"Processing paid invoice for subscription: {subscription_id}")
        
        # Get subscription details from Stripe
        import stripe
        try:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        except Exception as e:
            logger.error(f"Failed to retrieve Stripe subscription: {str(e)}")
            raise
        
        # Find our internal subscription
        subscriptions = await self.subscription_manager.get_subscriptions_by_provider_id(
            provider='stripe',
            provider_subscription_id=subscription_id
        )
        
        if not subscriptions:
            logger.warning(f"No matching subscription found for Stripe ID: {subscription_id}")
            return
        
        subscription = subscriptions[0]
        
        # Update subscription period
        period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
        period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        
        logger.info(f"Updating subscription period: {period_start} to {period_end}")
        subscription = await self.subscription_manager.update_subscription_period(
            subscription_id=subscription.subscription_id,
            period_start=period_start,
            period_end=period_end
        )
        
        # Allocate renewal credits
        plan = await self.subscription_manager.get_plan(subscription.plan_id)
        if plan:
            logger.info(f"Allocating renewal credits: {plan.credits_per_cycle} to {subscription.username}")
            await self.credit_integration.allocate_subscription_credits(
                username=subscription.username,
                amount=plan.credits_per_cycle,
                subscription_id=subscription.subscription_id,
                metadata={
                    'event': 'subscription_renewed',
                    'plan_id': plan.plan_id,
                    'plan_name': plan.name,
                    'invoice_id': invoice.get('id'),
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat()
                }
            )
        else:
            logger.error(f"Plan not found for renewal: {subscription.plan_id}")
    
    async def _handle_subscription_updated(self, event: Dict[str, Any]) -> None:
        """Handle subscription updates (plan changes, etc.)"""
        stripe_subscription = event['data']['object']
        subscription_id = stripe_subscription.get('id')
        
        logger.info(f"Processing subscription update: {subscription_id}")
        
        subscriptions = await self.subscription_manager.get_subscriptions_by_provider_id(
            provider='stripe',
            provider_subscription_id=subscription_id
        )
        
        if not subscriptions:
            logger.warning(f"No matching subscription found for update: {subscription_id}")
            return
        
        subscription = subscriptions[0]
        
        # Update status
        status = stripe_subscription.get('status')
        cancel_at_period_end = stripe_subscription.get('cancel_at_period_end', False)
        period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        
        logger.info(f"Updating subscription status: {status}, "
                   f"cancel_at_period_end: {cancel_at_period_end}")
        
        subscription.status = status
        subscription.cancel_at_period_end = cancel_at_period_end
        subscription.current_period_end = period_end
        
        await self.subscription_manager.update_subscription_status(
            subscription_id=subscription.subscription_id,
            status=status
        )
    
    async def _handle_subscription_deleted(self, event: Dict[str, Any]) -> None:
        """Handle subscription cancellation"""
        stripe_subscription = event['data']['object']
        subscription_id = stripe_subscription.get('id')
        
        logger.info(f"Processing subscription deletion: {subscription_id}")
        
        subscriptions = await self.subscription_manager.get_subscriptions_by_provider_id(
            provider='stripe',
            provider_subscription_id=subscription_id
        )
        
        if not subscriptions:
            logger.warning(f"No matching subscription found for deletion: {subscription_id}")
            return
        
        subscription = subscriptions[0]
        
        logger.info(f"Cancelling subscription: {subscription.subscription_id}")
        await self.subscription_manager.update_subscription_status(
            subscription_id=subscription.subscription_id,
            status='canceled'
        )
