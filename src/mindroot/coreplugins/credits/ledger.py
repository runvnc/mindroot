from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from .models import CreditTransaction
from .storage import CreditStorage

class InsufficientCreditsError(Exception):
    pass

class CreditLedger:
    """Manages credit transactions and balances.
    Ensures consistency and provides high-level credit operations."""
    
    def __init__(self, storage: CreditStorage):
        self._storage = storage

    async def record_allocation(self, username: str, amount: float,
                              source: str, reference_id: str,
                              metadata: Optional[Dict] = None) -> float:
        """Record a credit allocation (positive credit change)"""
        if amount <= 0:
            raise ValueError("Allocation amount must be positive")

        current_balance = await self._storage.get_latest_balance(username)
        new_balance = current_balance + amount

        transaction = CreditTransaction(
            timestamp=datetime.now(),
            username=username,
            amount=amount,
            balance=new_balance,
            type='allocation',
            source=source,
            reference_id=reference_id,
            metadata=metadata or {}
        )

        await self._storage.store_transaction(transaction)
        return new_balance

    async def record_usage(self, username: str, amount: float,
                          source: str, reference_id: str,
                          metadata: Optional[Dict] = None,
                          allow_negative: bool = False) -> float:
        """Record a credit usage (negative credit change)"""
        if amount <= 0:
            raise ValueError("Usage amount must be positive")

        current_balance = await self._storage.get_latest_balance(username)
        new_balance = current_balance - amount

        if not allow_negative and new_balance < 0:
            raise InsufficientCreditsError(
                f"Insufficient credits: {current_balance} available, {amount} required"
            )

        transaction = CreditTransaction(
            timestamp=datetime.now(),
            username=username,
            amount=-amount,  # Negative for usage
            balance=new_balance,
            type='usage',
            source=source,
            reference_id=reference_id,
            metadata=metadata or {}
        )

        await self._storage.store_transaction(transaction)
        return new_balance

    async def record_refund(self, username: str, amount: float,
                           source: str, reference_id: str,
                           original_transaction_id: str,
                           metadata: Optional[Dict] = None) -> float:
        """Record a credit refund (reversal of usage)"""
        if amount <= 0:
            raise ValueError("Refund amount must be positive")

        current_balance = await self._storage.get_latest_balance(username)
        new_balance = current_balance + amount

        transaction = CreditTransaction(
            timestamp=datetime.now(),
            username=username,
            amount=amount,
            balance=new_balance,
            type='refund',
            source=source,
            reference_id=reference_id,
            metadata={
                **(metadata or {}),
                'original_transaction_id': original_transaction_id
            }
        )

        await self._storage.store_transaction(transaction)
        return new_balance

    async def get_balance(self, username: str) -> float:
        """Get current credit balance"""
        return await self._storage.get_latest_balance(username)

    async def get_balance_at(self, username: str, at_date: date) -> float:
        """Get credit balance at a specific date"""
        return await self._storage.get_balance_at(username, at_date)

    async def get_transactions(self, username: str,
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None) -> List[CreditTransaction]:
        """Get transaction history"""
        return await self._storage.get_transactions(username, start_date, end_date)

    async def check_credits_available(self, username: str, 
                                    required_amount: float) -> Tuple[bool, float]:
        """Check if user has sufficient credits
        
        Returns:
            Tuple of (bool: has_sufficient, float: current_balance)
        """
        current_balance = await self.get_balance(username)
        return current_balance >= required_amount, current_balance

    async def get_usage_summary(self, username: str,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> Dict:
        """Get summary of credit usage"""
        transactions = await self.get_transactions(username, start_date, end_date)
        
        summary = {
            'total_allocated': 0.0,
            'total_used': 0.0,
            'total_refunded': 0.0,
            'usage_by_source': {},
            'allocations_by_source': {}
        }

        for txn in transactions:
            if txn.type == 'allocation':
                summary['total_allocated'] += txn.amount
                if txn.source not in summary['allocations_by_source']:
                    summary['allocations_by_source'][txn.source] = 0.0
                summary['allocations_by_source'][txn.source] += txn.amount
                
            elif txn.type == 'usage':
                summary['total_used'] += abs(txn.amount)
                if txn.source not in summary['usage_by_source']:
                    summary['usage_by_source'][txn.source] = 0.0
                summary['usage_by_source'][txn.source] += abs(txn.amount)
                
            elif txn.type == 'refund':
                summary['total_refunded'] += txn.amount

        return summary
