"""Scheduler commands - agent-facing commands for scheduling."""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from lib.providers.commands import command
from lib.providers.services import service_manager


@command()
async def schedule_command(
    cmd: str,
    schedule: str,
    args: Dict[str, Any] = None,
    schedule_name: str = None,
    context=None
) -> Dict:
    """Schedule a command to run at a specific time or interval.
    
    Parameters:
    cmd - String. The command name to execute.
    schedule - String. When to run. Supports:
        - Cron expressions: "0 8 * * *" (8 AM daily)
        - Human readable: "in 5 minutes", "tomorrow at 8 am", 
          "every day at 9:00", "every 30 minutes", "weekly on monday at 9:00"
    args - Object. Arguments to pass to the command (optional).
    schedule_name - String. Friendly name for this schedule (optional).
    
    Returns:
    Object with schedule_id and next_run time.
    
    Example:
    { "schedule_command": { 
        "cmd": "continue_job", 
        "schedule": "8 am tomorrow",
        "args": { "job_id": "job_abc123" }
    }}
    
    Example with cron:
    { "schedule_command": {
        "cmd": "cleanup_jobs",
        "schedule": "0 2 * * *",
        "args": { "older_than_days": 30 },
        "schedule_name": "Daily job cleanup"
    }}
    """
    username = getattr(context, 'username', None) if context else None
    agent_name = getattr(context, 'agent_name', None) if context else None
    
    result = await service_manager.create_schedule(
        command=cmd,
        schedule=schedule,
        args=args,
        schedule_name=schedule_name,
        username=username,
        agent_name=agent_name,
        context=context
    )
    
    return result


@command()
async def list_schedules(
    status: str = None,
    context=None
) -> Dict:
    """List all scheduled commands.
    
    Parameters:
    status - String. Filter by status: "active", "paused", or None for all.
    
    Returns:
    List of schedule objects with id, name, command, next_run, etc.
    
    Example:
    { "list_schedules": {} }
    
    Example with filter:
    { "list_schedules": { "status": "active" } }
    """
    username = getattr(context, 'username', None) if context else None
    
    schedules = await service_manager.list_schedules(
        username=username,
        status=status,
        context=context
    )
    
    # Format for display
    formatted = []
    for s in schedules:
        formatted.append({
            'id': s['id'],
            'name': s.get('name', s['id']),
            'command': s['command'],
            'schedule': s.get('schedule_string', ''),
            'next_run': s.get('next_run'),
            'last_run': s.get('last_run'),
            'status': 'active' if s.get('enabled', True) else 'paused',
            'run_count': s.get('run_count', 0),
            'error_count': s.get('error_count', 0)
        })
    
    return {'schedules': formatted, 'count': len(formatted)}


@command()
async def cancel_schedule(schedule_id: str, context=None) -> Dict:
    """Cancel a scheduled command.
    
    Parameters:
    schedule_id - String. The ID of the schedule to cancel.
    
    Returns:
    Status of the cancellation.
    
    Example:
    { "cancel_schedule": { "schedule_id": "sched_abc123" } }
    """
    result = await service_manager.cancel_schedule(
        schedule_id=schedule_id,
        context=context
    )
    return result


@command()
async def pause_schedule(schedule_id: str, context=None) -> Dict:
    """Pause a scheduled command (can be resumed later).
    
    Parameters:
    schedule_id - String. The ID of the schedule to pause.
    
    Returns:
    Status of the pause operation.
    
    Example:
    { "pause_schedule": { "schedule_id": "sched_abc123" } }
    """
    result = await service_manager.pause_schedule(
        schedule_id=schedule_id,
        context=context
    )
    return result


@command()
async def resume_schedule(schedule_id: str, context=None) -> Dict:
    """Resume a paused schedule.
    
    Parameters:
    schedule_id - String. The ID of the schedule to resume.
    
    Returns:
    Status and next run time.
    
    Example:
    { "resume_schedule": { "schedule_id": "sched_abc123" } }
    """
    result = await service_manager.resume_schedule(
        schedule_id=schedule_id,
        context=context
    )
    return result


@command()
async def get_schedule_history(
    schedule_id: str = None,
    days: int = 7,
    context=None
) -> Dict:
    """Get execution history for scheduled commands.
    
    Parameters:
    schedule_id - String. Filter to a specific schedule (optional).
    days - Integer. Number of days of history to retrieve (default: 7).
    
    Returns:
    List of execution records with timestamps, success status, and results.
    
    Example:
    { "get_schedule_history": { "days": 3 } }
    
    Example for specific schedule:
    { "get_schedule_history": { "schedule_id": "sched_abc123" } }
    """
    history = await service_manager.get_schedule_history(
        schedule_id=schedule_id,
        days=days,
        context=context
    )
    
    return {'history': history, 'count': len(history)}
