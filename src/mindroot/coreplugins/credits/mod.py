from datetime import datetime, date
from typing import Optional, Dict
from pathlib import Path
from lib.providers.services import service
from lib.providers.commands import command
from lib.providers.hooks import hook
from .models import CreditTransaction, CreditRatioConfig
from .storage import CreditStorage
from .ledger import CreditLedger, InsufficientCreditsError
from .conversion import CreditUsageHandler, CreditPolicy

# Initialize global instances
_storage = None
_ledger = None
_ratio_config = None
_credit_policy = None
_usage_handler = None

async def init_credit_system(base_path: str):
    """Initialize the credit system"""
    global _storage, _ledger, _ratio_config, _credit_policy, _usage_handler
    
    _storage = CreditStorage(base_path)
    _ledger = CreditLedger(_storage)
    _ratio_config = CreditRatioConfig()
    _credit_policy = CreditPolicy(_ledger, _ratio_config)
    _usage_handler = CreditUsageHandler(_ledger, _ratio_config)
    
    # Register the credit usage handler with the usage tracking system
    from mindroot.coreplugins.usage.mod import register_usage_handler
    await register_usage_handler(_usage_handler)
    
    return _ledger

@hook()
async def startup(app, context=None):
    """Startup tasks"""
    await init_credit_system(Path.cwd() / 'data' / 'credits')


@service()
async def allocate_credits(username: str, amount: float,
                          source: str, reference_id: str,
                          metadata: Optional[Dict] = None,
                          context=None) -> float:
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
    return await _ledger.record_allocation(
        username, amount, source, reference_id, metadata
    )

@service()
async def get_credit_balance(username: str, context=None) -> float:
    """Get current credit balance for a user.
    
    Example:
        balance = await get_credit_balance('user123')
    """
    return await _ledger.get_balance(username)

@service()
async def check_credits_available(username: str, required_amount: float,
                                context=None) -> Dict:
    """Check if user has sufficient credits.
    
    Returns:
        Dict with 'has_sufficient' and 'current_balance' keys
    """
    has_sufficient, balance = await _ledger.check_credits_available(
        username, required_amount
    )
    return {
        'has_sufficient': has_sufficient,
        'current_balance': balance
    }

@service()
async def set_credit_ratio(ratio: float, plugin_id: Optional[str] = None,
                          cost_type_id: Optional[str] = None,
                          model_id: Optional[str] = None,
                          context=None):
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
    _ratio_config.set_ratio(ratio, plugin_id, cost_type_id, model_id)

@service()
async def get_credit_ratios(context=None) -> Dict:
    """Get current credit ratio configuration."""
    return _ratio_config.get_config()

async def get_credit_report(username: str,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           context=None) -> Dict:
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
    
    transactions = await _ledger.get_transactions(username, start, end)
    summary = await _ledger.get_usage_summary(username, start, end)
    current_balance = await _ledger.get_balance(username)
    
    return {
        'username': username,
        'current_balance': current_balance,
        'summary': summary,
        'transactions': [t.to_dict() for t in transactions]
    }

async def estimate_credits(plugin_id: str, cost_type_id: str,
                         estimated_cost: float,
                         model_id: Optional[str] = None,
                         context=None) -> Dict:
    """Estimate credits needed for an operation.
    
    Example:
        estimate = await estimate_credits(
            'gpt4',
            'gpt4.input_tokens',
            0.01,  # $0.01
            'gpt-4-1106-preview'
        )
    """
    credits = _credit_policy.estimate_credits_needed(
        plugin_id, cost_type_id, estimated_cost, model_id
    )
    
    return {
        'estimated_cost': estimated_cost,
        'credits_required': credits,
        'ratio_used': credits / estimated_cost
    }
