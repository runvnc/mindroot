from pathlib import Path
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Iterator
from .models import CreditTransaction

class CreditStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _get_user_dir(self, username: str) -> Path:
        """Get the user's credit directory"""
        return self.base_path / 'data' / 'credits' / username

    def _get_month_dir(self, username: str, timestamp: datetime) -> Path:
        """Get the monthly transaction directory"""
        user_dir = self._get_user_dir(username)
        return user_dir / 'transactions' / timestamp.strftime('%Y-%m')

    def _get_balance_file(self, username: str, month_date: date) -> Path:
        """Get the monthly balance snapshot file"""
        user_dir = self._get_user_dir(username)
        balance_dir = user_dir / 'balances'
        balance_dir.mkdir(parents=True, exist_ok=True)
        return balance_dir / f"{month_date.strftime('%Y-%m')}.json"

    async def store_transaction(self, transaction: CreditTransaction) -> None:
        """Store a credit transaction"""
        month_dir = self._get_month_dir(transaction.username, transaction.timestamp)
        month_dir.mkdir(parents=True, exist_ok=True)
        
        transaction_file = month_dir / 'transactions.jsonl'
        
        with open(transaction_file, 'a') as f:
            f.write(json.dumps(transaction.to_dict()) + '\n')

        # Update monthly balance snapshot
        balance_file = self._get_balance_file(
            transaction.username, 
            transaction.timestamp.date().replace(day=1)
        )
        
        try:
            with open(balance_file, 'r') as f:
                balance_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            balance_data = {'balance': 0.0, 'last_transaction': None}
        
        balance_data['balance'] = transaction.balance
        balance_data['last_transaction'] = transaction.transaction_id
        
        with open(balance_file, 'w') as f:
            json.dump(balance_data, f)

    def _iter_month_files(self, username: str, 
                         start_date: Optional[date] = None,
                         end_date: Optional[date] = None) -> Iterator[Path]:
        """Iterate through monthly transaction files"""
        user_dir = self._get_user_dir(username)
        transactions_dir = user_dir / 'transactions'
        
        if not transactions_dir.exists():
            return

        for month_dir in sorted(transactions_dir.iterdir()):
            if not month_dir.is_dir():
                continue
                
            try:
                month_date = datetime.strptime(month_dir.name, '%Y-%m').date()
                if start_date and month_date < start_date.replace(day=1):
                    continue
                if end_date and month_date > end_date.replace(day=1):
                    continue
                    
                transaction_file = month_dir / 'transactions.jsonl'
                if transaction_file.exists():
                    yield transaction_file
            except ValueError:
                continue

    async def get_transactions(self, username: str,
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None) -> List[CreditTransaction]:
        """Get credit transactions for a user within date range"""
        transactions = []
        
        for file_path in self._iter_month_files(username, start_date, end_date):
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        transaction = CreditTransaction.from_dict(data)
                        
                        if start_date and transaction.timestamp.date() < start_date:
                            continue
                        if end_date and transaction.timestamp.date() > end_date:
                            continue
                            
                        transactions.append(transaction)
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return sorted(transactions, key=lambda t: t.timestamp)

    async def get_latest_balance(self, username: str) -> float:
        """Get the user's latest balance"""
        user_dir = self._get_user_dir(username)
        balance_dir = user_dir / 'balances'
        
        if not balance_dir.exists():
            return 0.0
        
        # Find most recent balance file
        balance_files = sorted(balance_dir.glob('*.json'), reverse=True)
        
        for file_path in balance_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data['balance']
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                continue
        
        return 0.0

    async def get_balance_at(self, username: str, at_date: date) -> float:
        """Get the user's balance at a specific date"""
        # Find the most recent balance snapshot before the date
        balance_file = self._get_balance_file(username, at_date.replace(day=1))
        
        try:
            with open(balance_file, 'r') as f:
                data = json.load(f)
                return data['balance']
        except (FileNotFoundError, json.JSONDecodeError):
            # If no snapshot, calculate from all previous transactions
            transactions = await self.get_transactions(
                username, end_date=at_date
            )
            return transactions[-1].balance if transactions else 0.0
