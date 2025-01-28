from datetime import date, datetime
from typing import Dict, Optional
from .storage import UsageStorage

class UsageReport:
    def __init__(self, storage: UsageStorage):
        self.storage = storage

    async def get_user_report(self, username: str,
                            start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> Dict:
        """Generate a complete usage report for a user"""
        usage_records = await self.storage.get_usage(username, start_date, end_date)
        total_cost = await self.storage.get_total_cost(username, start_date, end_date)

        # Group by plugin, cost type, and model
        grouped_usage = {}
        for record in usage_records:
            plugin_id = record['plugin_id']
            cost_type = record['cost_type_id']
            model_id = record.get('model_id')
            
            if plugin_id not in grouped_usage:
                grouped_usage[plugin_id] = {}
            
            if cost_type not in grouped_usage[plugin_id]:
                grouped_usage[plugin_id][cost_type] = {}

            model_key = model_id if model_id else '_default'
            if model_key not in grouped_usage[plugin_id][cost_type]:
                grouped_usage[plugin_id][cost_type][model_key] = {
                    'total_quantity': 0,
                    'total_cost': 0.0,
                    'events': []
                }
            
            group = grouped_usage[plugin_id][cost_type][model_key]
            group['total_quantity'] += record['quantity']
            group['total_cost'] += record.get('cost', 0.0)
            group['events'].append(record)

        return {
            'username': username,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'total_cost': total_cost,
            'usage_by_plugin': grouped_usage,
            'raw_records': usage_records
        }

    async def get_cost_summary(self, username: str,
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None) -> Dict:
        """Generate a simplified cost summary for a user"""
        usage_records = await self.storage.get_usage(username, start_date, end_date)
        total_cost = await self.storage.get_total_cost(username, start_date, end_date)

        # Summarize by plugin and model
        plugin_costs = {}
        for record in usage_records:
            plugin_id = record['plugin_id']
            model_id = record.get('model_id', '_default')
            cost = record.get('cost', 0.0)
            
            if plugin_id not in plugin_costs:
                plugin_costs[plugin_id] = {}
            
            if model_id not in plugin_costs[plugin_id]:
                plugin_costs[plugin_id][model_id] = 0.0
            
            plugin_costs[plugin_id][model_id] += cost

        return {
            'username': username,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'total_cost': total_cost,
            'costs_by_plugin': plugin_costs
        }

    async def get_daily_costs(self, username: str,
                            start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> Dict:
        """Generate daily cost breakdown for a user"""
        usage_records = await self.storage.get_usage(username, start_date, end_date)

        # Group by date, plugin, and model
        daily_costs = {}
        for record in usage_records:
            record_date = datetime.fromisoformat(record['timestamp']).date()
            date_str = record_date.isoformat()
            plugin_id = record['plugin_id']
            model_id = record.get('model_id', '_default')
            cost = record.get('cost', 0.0)
            
            if date_str not in daily_costs:
                daily_costs[date_str] = {
                    'total': 0.0,
                    'by_plugin': {}
                }
            
            if plugin_id not in daily_costs[date_str]['by_plugin']:
                daily_costs[date_str]['by_plugin'][plugin_id] = {}

            if model_id not in daily_costs[date_str]['by_plugin'][plugin_id]:
                daily_costs[date_str]['by_plugin'][plugin_id][model_id] = 0.0
            
            daily_costs[date_str]['total'] += cost
            daily_costs[date_str]['by_plugin'][plugin_id][model_id] += cost

        return {
            'username': username,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'daily_costs': daily_costs
        }
