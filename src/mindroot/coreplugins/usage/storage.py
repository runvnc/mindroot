from pathlib import Path
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Iterator, Any
import aiofiles
import asyncio
from .models import UsageEvent
from loguru import logger
import traceback

class UsageStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.config_path = self.base_path / 'config' / 'usage'
        self.data_path = self.base_path / 'data' / 'usage'
        logger.info(f"Usage storage initialized at {self.base_path}")
        self._ensure_paths()

    def _ensure_paths(self):
        """Create necessary directories if they don't exist"""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)

    async def _atomic_write_json(self, path: Path, data: Any):
        """Atomically write JSON data to a file"""
        temp_path = path.with_suffix('.tmp')
        async with aiofiles.open(temp_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
        temp_path.rename(path)

    async def _read_json(self, path: Path, default: Any = None) -> Any:
        """Read JSON data from a file, return default if file doesn't exist"""
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error(f"Failed to read JSON from {path}")
            return default

    async def load_cost_types(self) -> Dict:
        """Load cost type definitions"""
        return await self._read_json(self.config_path / 'cost_types.json', {})

    async def save_cost_type(self, cost_type_id: str, info: Dict):
        """Save a cost type definition"""
        cost_types = await self.load_cost_types()
        cost_types[cost_type_id] = info
        await self._atomic_write_json(self.config_path / 'cost_types.json', cost_types)

    async def load_costs(self) -> Dict:
        """Load cost configurations"""
        trace = traceback.format_stack()
        logger.info(f"Loading costs from {self.config_path} - {trace}")
        costs = await self._read_json(self.config_path / 'costs.json', {})
        logger.info(f"Loaded cost configurations: {costs}")
        return costs

    async def save_cost(self, plugin_id: str, cost_type_id: str, unit_cost: float, model_id: Optional[str] = None):
        """Save a cost configuration"""
        costs = await self.load_costs()
        if plugin_id not in costs:
            costs[plugin_id] = {}
        if cost_type_id not in costs[plugin_id]:
            costs[plugin_id][cost_type_id] = {}
        
        if model_id:
            if 'model_specific' not in costs[plugin_id][cost_type_id]:
                costs[plugin_id][cost_type_id]['model_specific'] = {}
            costs[plugin_id][cost_type_id]['model_specific'][model_id] = unit_cost
        else:
            costs[plugin_id][cost_type_id]['default'] = unit_cost
            
        await self._atomic_write_json(self.config_path / 'costs.json', costs)

    def _get_user_dir(self, username: str) -> Path:
        """Get the directory for a user's usage data"""
        user_dir = self.data_path / username
        user_dir.mkdir(exist_ok=True)
        return user_dir

    def _get_date_file(self, username: str, date_obj: date) -> Path:
        """Get the file path for a user's usage data on a specific date"""
        return self._get_user_dir(username) / f"usage_{date_obj.isoformat()}.jsonl"

    async def store_event(self, event: UsageEvent, cost: float):
        """Store a usage event with its calculated cost"""
        file_path = self._get_date_file(event.username, event.timestamp.date())
        
        event_dict = event.to_dict()
        event_dict['cost'] = cost

        async with aiofiles.open(file_path, 'a') as f:
            await f.write(json.dumps(event_dict) + '\n')

    async def get_usage(self, username: str, start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> List[Dict]:
        """Get usage records for a user within date range"""
        usage_records = []
        user_dir = self._get_user_dir(username)
        
        if not user_dir.exists():
            return []

        for file_path in sorted(user_dir.glob("usage_*.jsonl")):
            try:
                file_date = date.fromisoformat(file_path.stem.replace('usage_', ''))
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
                    
                async with aiofiles.open(file_path, 'r') as f:
                    async for line in f:
                        try:
                            record = json.loads(line)
                            record_date = datetime.fromisoformat(record['timestamp']).date()
                            
                            if start_date and record_date < start_date:
                                continue
                            if end_date and record_date > end_date:
                                continue
                                
                            usage_records.append(record)
                        except (json.JSONDecodeError, KeyError):
                            continue
                            
            except ValueError:
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
