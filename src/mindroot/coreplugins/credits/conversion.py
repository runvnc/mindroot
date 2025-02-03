from typing import Dict, Optional
from datetime import datetime
from .models import CreditRatioConfig
from .ledger import CreditLedger, InsufficientCreditsError
from mindroot.coreplugins.usage.models import UsageEvent 

class CreditUsageHandler:
    """Converts usage costs to credits and records credit transactions."""

    def __init__(self, ledger: CreditLedger, ratio_config: CreditRatioConfig, base_path: str):
        self.ledger = ledger
        self.ratio_config = ratio_config
        self.base_path = base_path

    async def _calculate_credit_cost(self, event: UsageEvent, monetary_cost: float) -> float:
        """Convert monetary cost to credit cost using configured ratios"""
        ratio = await self.ratio_config.get_ratio(
            plugin_id=event.plugin_id,
            cost_type_id=event.cost_type_id,
            model_id=event.model_id
        )
        print("Monetary cost is", monetary_cost)
        print("Ratio config is", self.ratio_config)
        print(f"got ratio for {event.plugin_id} and {event.cost_type_id} and {event.model_id} it is {ratio}")
        return monetary_cost * ratio

    async def handle_usage(self, plugin_id: str, cost_type_id: str, quantity: float, 
                         metadata: dict, context=None, model_id: Optional[str] = None) -> None:
        """Handle a usage event by converting cost to credits and recording transaction"""
        event = UsageEvent(
            timestamp=datetime.now(),
            plugin_id=plugin_id,
            cost_type_id=cost_type_id,
            quantity=quantity,
            metadata=metadata,
            username=context.username,
            model_id=model_id,
            session_id=context.log_id
        )

        # Get cost from usage tracker
        #from mindroot.coreplugins.usage.storage import UsageStorage
        #from mindroot.coreplugins.usage.handlers import UsageTracker

        #storage = UsageStorage(self.base_path)
        #tracker = UsageTracker(storage)
        monetary_cost = await context.get_cost(plugin_id, cost_type_id, model_id) * quantity
        #monetary_cost = await tracker.get_cost(plugin_id, cost_type_id, model_id) * quantity

        credit_cost = await self._calculate_credit_cost(event, monetary_cost)
        
        try:
            await self.ledger.record_usage(
                username=event.username,
                amount=credit_cost,
                source='usage_deduction',
                reference_id=event.session_id,
                metadata={
                    'plugin_id': event.plugin_id,
                    'cost_type_id': event.cost_type_id,
                    'model_id': event.model_id,
                    'monetary_cost': monetary_cost,
                    'credit_ratio': credit_cost / monetary_cost if monetary_cost else 0,
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
    
    def __init__(self, ledger: CreditLedger, ratio_config: CreditRatioConfig, base_path: str):
        self.ledger = ledger
        self.ratio_config = ratio_config

    async def check_operation_allowed(self, username: str, 
                                    plugin_id: str,
                                    cost_type_id: str,
                                    estimated_cost: float,
                                    model_id: Optional[str] = None) -> bool:
        """Check if an operation should be allowed based on estimated cost"""
        # Convert monetary cost to credits
        ratio = await self.ratio_config.get_ratio(plugin_id, cost_type_id, model_id)
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

    async def estimate_credits_needed(self, plugin_id: str,
                                   cost_type_id: str,
                                   estimated_cost: float,
                                   model_id: Optional[str] = None) -> float:
        """Estimate credits needed for an operation"""
        ratio = await self.ratio_config.get_ratio(plugin_id, cost_type_id, model_id)
        return estimated_cost * ratio
