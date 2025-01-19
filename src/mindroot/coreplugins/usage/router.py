from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import date
from typing import Optional
from lib.templates import render
from .handlers import UsageTracker
from .reporting import UsageReport
from .mod import _tracker, _report
from lib.route_decorators import requires_role

router = APIRouter( dependencies=[requires_role('admin')] )

@router.get("/admin/usage")
async def usage_admin(request: Request):
    """Admin interface for usage tracking configuration"""
    _tracker = request.app.state._tracker
    registry = _tracker.get_registry()
    cost_config = _tracker.get_cost_config()
    
    template_data = {
        "cost_types": registry.list_types(),
        "current_costs": cost_config.get_all_costs()
    }
    
    html = await render('usage', template_data)
    return HTMLResponse(html)

@router.post("/api/admin/usage/costs")
async def update_costs(request: Request):
    """Update cost configuration"""
    try:
        _tracker = request.app.state._tracker

        data = await request.json()
        plugin_id = data.get('plugin_id')
        cost_type_id = data.get('cost_type_id')
        unit_cost = float(data.get('unit_cost', 0))
        
        if not all([plugin_id, cost_type_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        _tracker.get_cost_config().set_cost(plugin_id, cost_type_id, unit_cost)
        return JSONResponse({"status": "success"})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/usage/report/{username}")
async def get_user_report(
                        request: Request,
                        username: str, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None):
    """Get usage report for a specific user"""
    try:
        _report = request.app.state._report
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        report = await _report.get_user_report(username, start, end)
        return JSONResponse(report)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/usage/summary/{username}")
async def get_user_summary(
                         request: Request,
                         username: str,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None):
    """Get cost summary for a specific user"""
    try:
        _report = request.app.state._report
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        summary = await _report.get_cost_summary(username, start, end)
        return JSONResponse(summary)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
