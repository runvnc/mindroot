from typing import Dict, Optional
from datetime import datetime
from .models import CreditRatioConfig
from .ledger import CreditLedger, InsufficientCreditsError
from mindroot.coreplugins.usage.models import UsageEvent
from mindroot.coreplugins.usage.handlers import UsageHandler

class CreditUsageHandler(UsageHandler):
    """Converts usage costs to credits and records credit transactions."""
    
    def __init__(self, ledger: CreditLedger, ratio_config: CreditRatioConfig):
        self.ledger = ledger
        self.ratio_config = ratio_config

    def _calculate_credit_cost(self, event: UsageEvent, monetary_cost: float) -> float:
        """Convert monetary cost to credit cost using configured ratios"""
        ratio = self.ratio_config.get_ratio(
            plugin_id=event.plugin_id,
            cost_type_id=event.cost_type_id,
            model_id=event.model_id
        )
        return monetary_cost * ratio

    async def handle_usage(self, event: UsageEvent, monetary_cost: float):
        """Handle a usage event by converting cost to credits and recording transaction"""
        credit_cost = self._calculate_credit_cost(event, monetary_cost)
        
        try:
            await self.ledger.record_usage(
                username=event.username,
                amount=credit_cost,
                source='usage_deduction',
                reference_id=event.request_id,
                metadata={
                    'plugin_id': event.plugin_id,
                    'cost_type_id': event.cost_type_id,
                    'model_id': event.model_id,
                    'monetary_cost': monetary_cost,
                    'credit_ratio': credit_cost / monetary_cost,
                    'quantity': event.quantity,
                    'original_metadata': event.metadata
                }
            )
        except InsufficientCreditsError as e:
            # Here you might want to implement specific handling for insufficient credits
            # For now, we'll just re-raise the exception
            raise

class CreditPolicy:
    """Encapsulates credit-related business rules and policies"""
    
    def __init__(self, ledger: CreditLedger, ratio_config: CreditRatioConfig):
        self.ledger = ledger
        self.ratio_config = ratio_config

    async def check_operation_allowed(self, username: str, 
                                    plugin_id: str,
                                    cost_type_id: str,
                                    estimated_cost: float,
                                    model_id: Optional[str] = None) -> bool:
        """Check if an operation should be allowed based on estimated cost"""
        # Convert monetary cost to credits
        ratio = self.ratio_config.get_ratio(plugin_id, cost_type_id, model_id)
        estimated_credits = estimated_cost * ratio
        
        # Check if user has sufficient credits
        has_credits, current_balance = await self.ledger.check_credits_available(
            username, estimated_credits
        )
        
        return has_credits

    async def get_user_limits(self, username: str) -> Dict:
        """Get user's credit limits and current usage"""
        current_balance = await self.ledger.get_balance(username)
        
        # You could extend this with more sophisticated limit calculations
        return {
            'current_balance': current_balance,
            'can_use_services': current_balance > 0
        }

    def estimate_credits_needed(self, plugin_id: str,
                              cost_type_id: str,
                              estimated_cost: float,
                              model_id: Optional[str] = None) -> float:
        """Estimate credits needed for an operation"""
        ratio = self.ratio_config.get_ratio(plugin_id, cost_type_id, model_id)
        return estimated_cost * ratio
