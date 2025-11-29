"""Scheduler HTTP routes for web UI."""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from lib.providers.services import service_manager
from lib.auth import get_current_user

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class CreateScheduleRequest(BaseModel):
    command: str
    schedule: str
    args: Optional[dict] = None
    name: Optional[str] = None
    agent_name: Optional[str] = None


class ScheduleIdRequest(BaseModel):
    schedule_id: str


@router.get("/schedules")
async def get_schedules(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get all schedules for the current user."""
    try:
        schedules = await service_manager.list_schedules(
            username=user.username if user else None,
            status=status,
            context=None
        )
        return {"schedules": schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules")
async def create_schedule(
    request: CreateScheduleRequest,
    user: dict = Depends(get_current_user)
):
    """Create a new schedule."""
    try:
        result = await service_manager.create_schedule(
            command=request.command,
            schedule=request.schedule,
            args=request.args,
            schedule_name=request.name,
            username=user.username if user else None,
            agent_name=request.agent_name,
            context=None
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific schedule."""
    try:
        schedule = await service_manager.get_schedule(
            schedule_id=schedule_id,
            context=None
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Check ownership
        user_roles = getattr(user, 'roles', []) or []
        if schedule.get('username') != user.username and 'admin' not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user: dict = Depends(get_current_user)
):
    """Cancel and delete a schedule."""
    try:
        # Check ownership first
        schedule = await service_manager.get_schedule(
            schedule_id=schedule_id,
            context=None
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        user_roles = getattr(user, 'roles', []) or []
        if schedule.get('username') != user.username and 'admin' not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await service_manager.cancel_schedule(
            schedule_id=schedule_id,
            context=None
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(
    schedule_id: str,
    user: dict = Depends(get_current_user)
):
    """Pause a schedule."""
    try:
        schedule = await service_manager.get_schedule(
            schedule_id=schedule_id,
            context=None
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        user_roles = getattr(user, 'roles', []) or []
        if schedule.get('username') != user.username and 'admin' not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await service_manager.pause_schedule(
            schedule_id=schedule_id,
            context=None
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(
    schedule_id: str,
    user: dict = Depends(get_current_user)
):
    """Resume a paused schedule."""
    try:
        schedule = await service_manager.get_schedule(
            schedule_id=schedule_id,
            context=None
        )
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        user_roles = getattr(user, 'roles', []) or []
        if schedule.get('username') != user.username and 'admin' not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await service_manager.resume_schedule(
            schedule_id=schedule_id,
            context=None
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    schedule_id: Optional[str] = None,
    days: int = 7,
    user: dict = Depends(get_current_user)
):
    """Get execution history."""
    try:
        history = await service_manager.get_schedule_history(
            schedule_id=schedule_id,
            days=days,
            context=None
        )
        
        # Filter to user's schedules unless admin
        user_roles = getattr(user, 'roles', []) or []
        if 'admin' not in user_roles:
            # Get user's schedule IDs
            user_schedules = await service_manager.list_schedules(
                username=user.username if user else None,
                context=None
            )
            user_schedule_ids = {s['id'] for s in user_schedules}
            history = [h for h in history if h.get('schedule_id') in user_schedule_ids]
        
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commands")
async def get_available_commands(
    user: dict = Depends(get_current_user)
):
    """Get list of commands that can be scheduled."""
    from lib.providers.commands import command_manager
    
    commands = []
    for name, func_list in command_manager.functions.items():
        # Get docstring from first implementation
        docstring = func_list[0].get('docstring', '') if func_list else ''
        commands.append({
            'name': name,
            'description': docstring.split('\n')[0] if docstring else '',
            'providers': [f['provider'] for f in func_list]
        })
    
    commands.sort(key=lambda c: c['name'])
    return {"commands": commands}
