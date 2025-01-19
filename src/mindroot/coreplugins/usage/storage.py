from pathlib import Path
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Iterator
from .models import UsageEvent

class UsageStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _get_user_dir(self, username: str) -> Path:
        return self.base_path / 'data' / 'usage' / username

    def _get_date_file(self, username: str, date_obj: date) -> Path:
        user_dir = self._get_user_dir(username)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / f"usage_{date_obj.isoformat()}.jsonl"

    async def store_event(self, event: UsageEvent, cost: float):
        """Store a usage event with its calculated cost"""
        file_path = self._get_date_file(event.username, event.timestamp.date())
        
        event_dict = event.to_dict()
        event_dict['cost'] = cost

        with open(file_path, 'a') as f:
            f.write(json.dumps(event_dict) + '\n')

    def _iter_date_files(self, username: str, start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> Iterator[Path]:
        """Iterate through date files for a user within date range"""
        user_dir = self._get_user_dir(username)
        if not user_dir.exists():
            print("Warning: Usage: User directory does not exist for user ", username, "user dir is: ", user_dir)
            return

        for file_path in sorted(user_dir.glob("usage_*.jsonl")):
            try:
                file_date = date.fromisoformat(file_path.stem.replace('usage_', ''))
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
                yield file_path
            except ValueError:
                continue

    async def get_usage(self, username: str, start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> List[Dict]:
        """Get usage records for a user within date range"""
        usage_records = []
        
        for file_path in self._iter_date_files(username, start_date, end_date):
            try:
                print("get_usage Found file", file_path)
                with open(file_path, 'r') as f:
                    for line in f:
                        record = json.loads(line)
                        record_date = datetime.fromisoformat(record['timestamp']).date()
                        
                        if start_date and record_date < start_date:
                            continue
                        if end_date and record_date > end_date:
                            continue
                            
                        usage_records.append(record)
            except (json.JSONDecodeError, KeyError):
                continue

        return usage_records

    async def get_total_cost(self, username: str, start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> float:
        """Calculate total cost for a user within date range"""
        total = 0.0
        records = await self.get_usage(username, start_date, end_date)
        
        for record in records:
            total += record.get('cost', 0.0)
            
        return total
