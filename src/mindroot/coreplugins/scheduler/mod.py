"""Scheduler module - core scheduling logic and services.

Provides cron-like scheduling for commands and tasks in MindRoot.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiofiles
import aiofiles.os
from pathlib import Path

from lib.providers.services import service, service_manager
from lib.providers.commands import command_manager
from lib.providers.hooks import hook
from lib.utils.debug import debug_box

# Schedule storage directory
SCHEDULE_DIR = "data/schedules"
ACTIVE_DIR = f"{SCHEDULE_DIR}/active"
PAUSED_DIR = f"{SCHEDULE_DIR}/paused"
COMPLETED_DIR = f"{SCHEDULE_DIR}/completed"
HISTORY_DIR = f"{SCHEDULE_DIR}/history"

# Ensure directories exist
os.makedirs(ACTIVE_DIR, exist_ok=True)
os.makedirs(PAUSED_DIR, exist_ok=True)
os.makedirs(COMPLETED_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# Scheduler state
scheduler_task = None
scheduler_running = asyncio.Event()

# In-memory cache of schedules for fast lookup
schedule_cache: Dict[str, Dict] = {}
cache_lock = asyncio.Lock()


def parse_cron_field(field: str, min_val: int, max_val: int) -> List[int]:
    """Parse a single cron field into a list of valid values."""
    if field == '*':
        return list(range(min_val, max_val + 1))
    
    values = set()
    for part in field.split(','):
        if '/' in part:
            # Step values: */5 or 1-10/2
            range_part, step = part.split('/')
            step = int(step)
            if range_part == '*':
                start, end = min_val, max_val
            elif '-' in range_part:
                start, end = map(int, range_part.split('-'))
            else:
                start = int(range_part)
                end = max_val
            values.update(range(start, end + 1, step))
        elif '-' in part:
            # Range: 1-5
            start, end = map(int, part.split('-'))
            values.update(range(start, end + 1))
        else:
            # Single value
            values.add(int(part))
    
    return sorted([v for v in values if min_val <= v <= max_val])


def parse_cron_expression(cron_expr: str) -> Dict[str, List[int]]:
    """Parse a cron expression into component lists.
    
    Format: minute hour day_of_month month day_of_week
    Example: "0 8 * * *" = 8:00 AM every day
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr}. Expected 5 fields.")
    
    return {
        'minutes': parse_cron_field(parts[0], 0, 59),
        'hours': parse_cron_field(parts[1], 0, 23),
        'days': parse_cron_field(parts[2], 1, 31),
        'months': parse_cron_field(parts[3], 1, 12),
        'weekdays': parse_cron_field(parts[4], 0, 6),  # 0 = Sunday
    }


def parse_human_schedule(schedule_str: str) -> Dict[str, Any]:
    """Parse human-readable schedule strings.
    
    Supported formats:
    - "8 am tomorrow"
    - "in 5 minutes"
    - "in 2 hours"
    - "every day at 9:00"
    - "every hour"
    - "every 30 minutes"
    - "daily at 8:00 am"
    - "weekly on monday at 9:00"
    """
    schedule_str = schedule_str.lower().strip()
    now = datetime.now()
    
    # "in X minutes/hours"
    if schedule_str.startswith('in '):
        parts = schedule_str[3:].split()
        if len(parts) >= 2:
            amount = int(parts[0])
            unit = parts[1].rstrip('s')  # Remove plural 's'
            if unit == 'minute':
                run_at = now + timedelta(minutes=amount)
            elif unit == 'hour':
                run_at = now + timedelta(hours=amount)
            elif unit == 'day':
                run_at = now + timedelta(days=amount)
            else:
                raise ValueError(f"Unknown time unit: {unit}")
            return {'type': 'once', 'run_at': run_at.isoformat()}
    
    # "tomorrow at X" or "X am/pm tomorrow"
    if 'tomorrow' in schedule_str:
        tomorrow = now + timedelta(days=1)
        # Extract time
        time_str = schedule_str.replace('tomorrow', '').replace('at', '').strip()
        hour, minute = parse_time_string(time_str)
        run_at = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return {'type': 'once', 'run_at': run_at.isoformat()}
    
    # "every X minutes/hours"
    if schedule_str.startswith('every '):
        rest = schedule_str[6:]
        
        # "every 30 minutes"
        if 'minute' in rest:
            parts = rest.split()
            interval = int(parts[0])
            return {'type': 'interval', 'interval_minutes': interval}
        
        # "every hour" or "every 2 hours"
        if 'hour' in rest:
            parts = rest.split()
            if parts[0] == 'hour':
                interval = 1
            else:
                interval = int(parts[0])
            return {'type': 'interval', 'interval_minutes': interval * 60}
        
        # "every day at X"
        if 'day' in rest:
            time_part = rest.split('at')[-1].strip() if 'at' in rest else '0:00'
            hour, minute = parse_time_string(time_part)
            return {'type': 'cron', 'cron': f"{minute} {hour} * * *"}
        
        # "every monday/tuesday/etc at X"
        weekdays = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        for i, day in enumerate(weekdays):
            if day in rest:
                time_part = rest.split('at')[-1].strip() if 'at' in rest else '9:00'
                hour, minute = parse_time_string(time_part)
                return {'type': 'cron', 'cron': f"{minute} {hour} * * {i}"}
    
    # "daily at X"
    if schedule_str.startswith('daily'):
        time_part = schedule_str.split('at')[-1].strip() if 'at' in schedule_str else '0:00'
        hour, minute = parse_time_string(time_part)
        return {'type': 'cron', 'cron': f"{minute} {hour} * * *"}
    
    # "weekly on X at Y"
    if schedule_str.startswith('weekly'):
        weekdays = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        for i, day in enumerate(weekdays):
            if day in schedule_str:
                time_part = schedule_str.split('at')[-1].strip() if 'at' in schedule_str else '9:00'
                hour, minute = parse_time_string(time_part)
                return {'type': 'cron', 'cron': f"{minute} {hour} * * {i}"}
    
    # Try parsing as cron expression directly
    if len(schedule_str.split()) == 5:
        return {'type': 'cron', 'cron': schedule_str}
    
    raise ValueError(f"Could not parse schedule: {schedule_str}")


def parse_time_string(time_str: str) -> tuple:
    """Parse time string like '8:00', '8 am', '14:30' into (hour, minute)."""
    time_str = time_str.strip().lower()
    
    # Handle am/pm
    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    time_str = time_str.replace('am', '').replace('pm', '').strip()
    
    if ':' in time_str:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    else:
        hour = int(time_str) if time_str else 0
        minute = 0
    
    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0
    
    return hour, minute


def get_next_cron_run(cron_parsed: Dict[str, List[int]], after: datetime = None) -> datetime:
    """Calculate the next run time for a cron schedule."""
    if after is None:
        after = datetime.now()
    
    # Start from the next minute
    current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    
    # Search for next valid time (limit to prevent infinite loop)
    for _ in range(525600):  # Max 1 year of minutes
        if (current.minute in cron_parsed['minutes'] and
            current.hour in cron_parsed['hours'] and
            current.day in cron_parsed['days'] and
            current.month in cron_parsed['months'] and
            # Python weekday(): 0=Monday, 6=Sunday
            # Cron weekday: 0=Sunday, 6=Saturday
            # Convert Python weekday to cron: (weekday + 1) % 7
            ((current.weekday() + 1) % 7) in cron_parsed['weekdays']):
            return current
        current += timedelta(minutes=1)
    
    raise ValueError("Could not find next run time within 1 year")


async def load_schedule(schedule_id: str) -> Optional[Dict]:
    """Load a schedule from disk."""
    for directory in [ACTIVE_DIR, PAUSED_DIR]:
        path = f"{directory}/{schedule_id}.json"
        if await aiofiles.os.path.exists(path):
            async with aiofiles.open(path, 'r') as f:
                return json.loads(await f.read())
    return None


async def save_schedule(schedule: Dict, status: str = 'active') -> None:
    """Save a schedule to disk."""
    schedule_id = schedule['id']
    directory = ACTIVE_DIR if status == 'active' else PAUSED_DIR
    path = f"{directory}/{schedule_id}.json"
    
    async with aiofiles.open(path, 'w') as f:
        await f.write(json.dumps(schedule, indent=2))
    
    # Update cache
    async with cache_lock:
        schedule_cache[schedule_id] = schedule


async def delete_schedule(schedule_id: str) -> bool:
    """Delete a schedule from disk."""
    for directory in [ACTIVE_DIR, PAUSED_DIR]:
        path = f"{directory}/{schedule_id}.json"
        if await aiofiles.os.path.exists(path):
            await aiofiles.os.remove(path)
            async with cache_lock:
                schedule_cache.pop(schedule_id, None)
            return True
    return False


async def load_all_schedules() -> List[Dict]:
    """Load all active schedules from disk."""
    schedules = []
    
    if await aiofiles.os.path.exists(ACTIVE_DIR):
        for filename in await aiofiles.os.listdir(ACTIVE_DIR):
            if filename.endswith('.json'):
                path = f"{ACTIVE_DIR}/{filename}"
                try:
                    async with aiofiles.open(path, 'r') as f:
                        schedule = json.loads(await f.read())
                        schedules.append(schedule)
                except Exception as e:
                    print(f"Error loading schedule {filename}: {e}")
    
    return schedules


async def record_execution(schedule: Dict, success: bool, result: Any = None, error: str = None) -> None:
    """Record a schedule execution in history."""
    history_entry = {
        'schedule_id': schedule['id'],
        'schedule_name': schedule.get('name', schedule['id']),
        'command': schedule['command'],
        'executed_at': datetime.now().isoformat(),
        'success': success,
        'result': str(result)[:1000] if result else None,
        'error': error
    }
    
    # Save to history file (one file per day)
    date_str = datetime.now().strftime('%Y-%m-%d')
    history_path = f"{HISTORY_DIR}/{date_str}.json"
    
    history = []
    if await aiofiles.os.path.exists(history_path):
        async with aiofiles.open(history_path, 'r') as f:
            try:
                history = json.loads(await f.read())
            except:
                history = []
    
    history.append(history_entry)
    
    async with aiofiles.open(history_path, 'w') as f:
        await f.write(json.dumps(history, indent=2))


@service()
async def create_schedule(
    command: str,
    schedule: str,
    args: Dict[str, Any] = None,
    schedule_name: str = None,
    username: str = None,
    agent_name: str = None,
    enabled: bool = True,
    context=None
) -> Dict:
    """Create a new scheduled command.
    
    Args:
        command: The command name to execute (from command_manager)
        schedule: Schedule string - cron expression or human-readable
        args: Arguments to pass to the command
        schedule_name: Optional friendly name for the schedule
        username: User who owns this schedule
        agent_name: Optional agent context for command execution
        enabled: Whether the schedule is active
        context: MindRoot context
    
    Returns:
        Dict with schedule_id and status
    """
    schedule_id = f"sched_{uuid.uuid4().hex[:12]}"
    
    if username is None and context:
        username = getattr(context, 'username', 'system')
    
    # Parse the schedule string
    try:
        parsed = parse_human_schedule(schedule)
    except ValueError as e:
        return {'error': str(e)}
    
    # Calculate next run time
    if parsed['type'] == 'once':
        next_run = parsed['run_at']
    elif parsed['type'] == 'cron':
        cron_parsed = parse_cron_expression(parsed['cron'])
        next_run = get_next_cron_run(cron_parsed).isoformat()
    elif parsed['type'] == 'interval':
        next_run = (datetime.now() + timedelta(minutes=parsed['interval_minutes'])).isoformat()
    
    schedule_data = {
        'id': schedule_id,
        'name': schedule_name or f"{command} schedule",
        'command': command,
        'args': args or {},
        'schedule_type': parsed['type'],
        'schedule_config': parsed,
        'schedule_string': schedule,
        'username': username,
        'agent_name': agent_name,
        'enabled': enabled,
        'created_at': datetime.now().isoformat(),
        'next_run': next_run,
        'last_run': None,
        'run_count': 0,
        'error_count': 0
    }
    
    await save_schedule(schedule_data, 'active' if enabled else 'paused')
    
    debug_box(f"Created schedule {schedule_id}: {command} @ {schedule}")
    
    return {'schedule_id': schedule_id, 'next_run': next_run, 'status': 'created'}


@service()
async def get_schedule(schedule_id: str, context=None) -> Optional[Dict]:
    """Get a schedule by ID."""
    return await load_schedule(schedule_id)


@service()
async def list_schedules(username: str = None, status: str = None, context=None) -> List[Dict]:
    """List all schedules, optionally filtered by username or status."""
    schedules = []
    
    directories = []
    if status is None or status == 'active':
        directories.append(ACTIVE_DIR)
    if status is None or status == 'paused':
        directories.append(PAUSED_DIR)
    
    for directory in directories:
        if await aiofiles.os.path.exists(directory):
            for filename in await aiofiles.os.listdir(directory):
                if filename.endswith('.json'):
                    path = f"{directory}/{filename}"
                    try:
                        async with aiofiles.open(path, 'r') as f:
                            schedule = json.loads(await f.read())
                            if username is None or schedule.get('username') == username:
                                schedule['status'] = 'active' if directory == ACTIVE_DIR else 'paused'
                                schedules.append(schedule)
                    except Exception as e:
                        print(f"Error loading schedule {filename}: {e}")
    
    # Sort by next_run
    schedules.sort(key=lambda s: s.get('next_run', ''))
    
    return schedules


@service()
async def pause_schedule(schedule_id: str, context=None) -> Dict:
    """Pause a schedule."""
    schedule = await load_schedule(schedule_id)
    if not schedule:
        return {'error': 'Schedule not found'}
    
    # Move from active to paused
    active_path = f"{ACTIVE_DIR}/{schedule_id}.json"
    if await aiofiles.os.path.exists(active_path):
        await aiofiles.os.remove(active_path)
    
    schedule['enabled'] = False
    await save_schedule(schedule, 'paused')
    
    return {'status': 'paused', 'schedule_id': schedule_id}


@service()
async def resume_schedule(schedule_id: str, context=None) -> Dict:
    """Resume a paused schedule."""
    schedule = await load_schedule(schedule_id)
    if not schedule:
        return {'error': 'Schedule not found'}
    
    # Move from paused to active
    paused_path = f"{PAUSED_DIR}/{schedule_id}.json"
    if await aiofiles.os.path.exists(paused_path):
        await aiofiles.os.remove(paused_path)
    
    # Recalculate next run time
    parsed = schedule['schedule_config']
    if parsed['type'] == 'cron':
        cron_parsed = parse_cron_expression(parsed['cron'])
        schedule['next_run'] = get_next_cron_run(cron_parsed).isoformat()
    elif parsed['type'] == 'interval':
        schedule['next_run'] = (datetime.now() + timedelta(minutes=parsed['interval_minutes'])).isoformat()
    
    schedule['enabled'] = True
    await save_schedule(schedule, 'active')
    
    return {'status': 'resumed', 'schedule_id': schedule_id, 'next_run': schedule['next_run']}


@service()
async def cancel_schedule(schedule_id: str, context=None) -> Dict:
    """Cancel and delete a schedule."""
    if await delete_schedule(schedule_id):
        return {'status': 'cancelled', 'schedule_id': schedule_id}
    return {'error': 'Schedule not found'}


@service()
async def get_schedule_history(schedule_id: str = None, days: int = 7, context=None) -> List[Dict]:
    """Get execution history for schedules."""
    history = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        history_path = f"{HISTORY_DIR}/{date_str}.json"
        
        if await aiofiles.os.path.exists(history_path):
            async with aiofiles.open(history_path, 'r') as f:
                try:
                    day_history = json.loads(await f.read())
                    if schedule_id:
                        day_history = [h for h in day_history if h['schedule_id'] == schedule_id]
                    history.extend(day_history)
                except:
                    pass
    
    # Sort by execution time, newest first
    history.sort(key=lambda h: h.get('executed_at', ''), reverse=True)
    
    return history


async def execute_scheduled_command(schedule: Dict) -> None:
    """Execute a scheduled command."""
    command_name = schedule['command']
    args = schedule.get('args', {})
    username = schedule.get('username', 'system')
    agent_name = schedule.get('agent_name')
    
    debug_box(f"Executing scheduled command: {command_name}")
    
    try:
        # Check if command exists
        if command_name not in command_manager.functions:
            raise ValueError(f"Command '{command_name}' not found")
        
        # Create a minimal context for command execution
        from lib.chatcontext import ChatContext
        context = ChatContext(command_manager, service_manager, username)
        context.username = username
        if agent_name:
            context.agent_name = agent_name
            context.agent = await service_manager.get_agent_data(agent_name)
        
        # Execute the command
        result = await command_manager.execute(command_name, **args, context=context)
        
        # Record success
        await record_execution(schedule, success=True, result=result)
        
        # Update schedule stats
        schedule['last_run'] = datetime.now().isoformat()
        schedule['run_count'] = schedule.get('run_count', 0) + 1
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error executing scheduled command {command_name}: {error_msg}")
        
        # Record failure
        await record_execution(schedule, success=False, error=error_msg)
        
        # Update error count
        schedule['error_count'] = schedule.get('error_count', 0) + 1
        schedule['last_error'] = error_msg
        schedule['last_run'] = datetime.now().isoformat()
    
    # Calculate next run time
    parsed = schedule['schedule_config']
    if parsed['type'] == 'once':
        # One-time schedule - move to completed
        await delete_schedule(schedule['id'])
        schedule['status'] = 'completed'
        completed_path = f"{COMPLETED_DIR}/{schedule['id']}.json"
        async with aiofiles.open(completed_path, 'w') as f:
            await f.write(json.dumps(schedule, indent=2))
    elif parsed['type'] == 'cron':
        cron_parsed = parse_cron_expression(parsed['cron'])
        schedule['next_run'] = get_next_cron_run(cron_parsed).isoformat()
        await save_schedule(schedule, 'active')
    elif parsed['type'] == 'interval':
        schedule['next_run'] = (datetime.now() + timedelta(minutes=parsed['interval_minutes'])).isoformat()
        await save_schedule(schedule, 'active')


async def scheduler_loop():
    """Main scheduler loop - checks for due schedules and executes them."""
    print("Scheduler loop started")
    
    while scheduler_running.is_set():
        try:
            now = datetime.now()
            schedules = await load_all_schedules()
            
            for schedule in schedules:
                if not schedule.get('enabled', True):
                    continue
                
                next_run_str = schedule.get('next_run')
                if not next_run_str:
                    continue
                
                try:
                    next_run = datetime.fromisoformat(next_run_str)
                except:
                    continue
                
                if next_run <= now:
                    # Time to execute!
                    asyncio.create_task(execute_scheduled_command(schedule))
            
            # Sleep for a short interval before checking again
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
            await asyncio.sleep(60)  # Back off on error
    
    print("Scheduler loop stopped")


@hook()
async def startup(app, context=None):
    """Start the scheduler when the plugin loads."""
    global scheduler_task
    print("Scheduler plugin starting...")
    scheduler_running.set()
    scheduler_task = asyncio.create_task(scheduler_loop())
    return {"status": "Scheduler started"}


@hook()
async def quit(context=None):
    """Stop the scheduler when the plugin stops."""
    global scheduler_task
    print("Scheduler plugin stopping...")
    scheduler_running.clear()
    
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await asyncio.wait_for(scheduler_task, timeout=5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
    
    print("Scheduler stopped")
    return {"status": "Scheduler stopped"}
