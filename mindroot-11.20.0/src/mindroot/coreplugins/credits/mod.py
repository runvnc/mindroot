from datetime import datetime, date
from typing import Optional, Dict
from pathlib import Path
from lib.providers.services import service
from lib.providers.commands import command
from lib.providers.hooks import hook
from lib.utils.debug import debug_box
from .models import CreditTransaction, CreditRatioConfig
from .storage import CreditStorage
from .ledger import CreditLedger
from .conversion import CreditUsageHandler, CreditPolicy
_usage_handler = None

class CreditsPlugin:

    def __init__(self, base_path: str):
        self.base_path = base_path

    def create_components(self):
        """Create fresh instances of all credit system components"""
        storage = CreditStorage(self.base_path)
        ratio_config = CreditRatioConfig(self.base_path)
        ledger = CreditLedger(storage)
        credit_policy = CreditPolicy(ledger, ratio_config, self.base_path)
        usage_handler = CreditUsageHandler(ledger, ratio_config, self.base_path)
        return (storage, ledger, ratio_config, credit_policy, usage_handler)

def get_base_path(context) -> str:
    """Get the base path for credit data storage"""
    return str(Path.cwd() / 'data' / 'credits')

@hook()
async def startup(app, context=None):
    """Startup tasks"""
    plugin = CreditsPlugin(get_base_path(context))
    _, _, _, _, usage_handler = plugin.create_components()
    global _usage_handler
    _usage_handler = usage_handler

@hook()
async def handle_usage(plugin_id: str, cost_type_id: str, quantity: float, metadata: dict, context=None, model_id: Optional[str]=None):
    """Handle usage tracking for credits system.
    This service is called by the usage plugin after tracking usage.
    """
    global _usage_handler
    if not _usage_handler:
        raise RuntimeError('Credits plugin not properly initialized')
    debug_box('Recording credit usage: {} {} {}'.format(plugin_id, cost_type_id, quantity))
    await _usage_handler.handle_usage(plugin_id, cost_type_id, quantity, metadata, context, model_id)

@service()
async def allocate_credits(username: str, amount: float, source: str, reference_id: str, metadata: Optional[Dict]=None, context=None) -> float:
    """Allocate credits to a user.
    
    Args:
        username: User to allocate credits to
        amount: Amount of credits to allocate
        source: Source of allocation (e.g., 'purchase', 'admin_grant')
        reference_id: External reference (e.g., payment ID)
        metadata: Additional information about allocation
        context: Request context
    
    Returns:
        float: New credit balance
    
    Example:
        new_balance = await allocate_credits(
            'user123',
            1000.0,
            'purchase',
            'payment_123',
            {'payment_method': 'stripe'}
        )
    """
    plugin = CreditsPlugin(get_base_path(context))
    _, ledger, _, _, _ = plugin.create_components()
    return await ledger.record_allocation(username, amount, source, reference_id, metadata)

@service()
async def get_credit_balance(username: str, context=None) -> float:
    """Get current credit balance for a user.
    
    Example:
        balance = await get_credit_balance('user123')
    """
    plugin = CreditsPlugin(get_base_path(context))
    _, ledger, _, _, _ = plugin.create_components()
    return await ledger.get_balance(username)

@service()
async def check_credits_available(username: str, required_amount: float, context=None) -> Dict:
    """Check if user has sufficient credits.
    
    Returns:
        Dict with 'has_sufficient' and 'current_balance' keys
    """
    plugin = CreditsPlugin(get_base_path(context))
    _, ledger, _, _, _ = plugin.create_components()
    has_sufficient, balance = await ledger.check_credits_available(username, required_amount)
    return {'has_sufficient': has_sufficient, 'current_balance': balance}

@service()
async def set_credit_ratio(ratio: float, plugin_id: Optional[str]=None, cost_type_id: Optional[str]=None, model_id: Optional[str]=None, context=None):
    """Set credit ratio for cost conversion.
    
    Args:
        ratio: Credits per unit cost
        plugin_id: Optional plugin identifier
        cost_type_id: Optional cost type identifier
        model_id: Optional model identifier
    
    Example:
        # Set global default ratio
        await set_credit_ratio(100.0)
        
        # Set model-specific ratio
        await set_credit_ratio(
            90.0,
            plugin_id='gpt4',
            cost_type_id='gpt4.input_tokens',
            model_id='gpt-4-1106-preview'
        )
    """
    plugin = CreditsPlugin(get_base_path(context))
    _, _, ratio_config, _, _ = plugin.create_components()
    await ratio_config.set_ratio(ratio, plugin_id, cost_type_id, model_id)

@service()
async def get_credit_ratios(context=None) -> Dict:
    """Get current credit ratio configuration."""
    plugin = CreditsPlugin(get_base_path(context))
    _, _, ratio_config, _, _ = plugin.create_components()
    return await ratio_config.get_config()

@service()
async def get_credit_report(username: str, start_date: Optional[str]=None, end_date: Optional[str]=None, context=None) -> Dict:
    """Get detailed credit report for a user.
    
    Args:
        username: User to get report for
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    
    Returns:
        Dict containing:
        - Current balance
        - Transaction history
        - Usage summary
    """
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    plugin = CreditsPlugin(get_base_path(context))
    _, ledger, _, _, _ = plugin.create_components()
    transactions = await ledger.get_transactions(username, start, end)
    summary = await ledger.get_usage_summary(username, start, end)
    current_balance = await ledger.get_balance(username)
    return {'username': username, 'current_balance': current_balance, 'summary': summary, 'transactions': [t.to_dict() for t in transactions]}

@service()
async def estimate_credits(plugin_id: str, cost_type_id: str, estimated_cost: float, model_id: Optional[str]=None, context=None) -> Dict:
    """Estimate credits needed for an operation.
    
    Example:
        estimate = await estimate_credits(
            'gpt4',
            'gpt4.input_tokens',
            0.01,  # $0.01
            'gpt-4-1106-preview'
        )
    """
    plugin = CreditsPlugin(get_base_path(context))
    _, _, _, credit_policy, _ = plugin.create_components()
    credits = await credit_policy.estimate_credits_needed(plugin_id, cost_type_id, estimated_cost, model_id)
    return {'estimated_cost': estimated_cost, 'credits_required': credits, 'ratio_used': credits / estimated_cost}