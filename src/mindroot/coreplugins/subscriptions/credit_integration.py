from typing import Dict, Any
from loguru import logger

class CreditIntegration:
    """Handles integration with the credits plugin for subscription-related credit operations"""
    
    def __init__(self):
        pass
    
    async def allocate_subscription_credits(self, username: str, amount: float, 
                                          subscription_id: str, metadata: Dict[str, Any]) -> float:
        """Allocate credits to a user based on their subscription
        
        Args:
            username: User to allocate credits to
            amount: Amount of credits to allocate
            subscription_id: Subscription ID for reference
            metadata: Additional information about the allocation
            
        Returns:
            float: New credit balance
        """
        try:
            # Import here to avoid circular imports
            from mindroot.coreplugins.credits.mod import allocate_credits
            
            # Add subscription-specific metadata
            allocation_metadata = {
                'source_type': 'subscription',
                **metadata
            }
            
            # Allocate credits
            new_balance = await allocate_credits(
                username=username,
                amount=amount,
                source='subscription',
                reference_id=subscription_id,
                metadata=allocation_metadata
            )
            
            logger.info(f"Allocated {amount} credits to {username} for subscription {subscription_id}")
            return new_balance
            
        except Exception as e:
            logger.error(f"Failed to allocate subscription credits: {str(e)}")
            raise
    
    async def check_credit_balance(self, username: str) -> float:
        """Get current credit balance for a user"""
        try:
            from mindroot.coreplugins.credits.mod import get_credit_balance
            return await get_credit_balance(username)
        except Exception as e:
            logger.error(f"Failed to check credit balance: {str(e)}")
            raise
