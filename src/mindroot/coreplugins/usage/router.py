from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import date
from typing import Optional
from lib.templates import render
from .storage import UsageStorage
from .handlers import UsageTracker
from .reporting import UsageReport
from lib.route_decorators import requires_role

router = APIRouter(dependencies=[requires_role('admin')])

def get_base_path():
    from pathlib import Path
    return str(Path.cwd())

@router.get("/admin/usage")
async def usage_admin(request: Request):
    """Admin interface for usage tracking configuration"""
    storage = UsageStorage(get_base_path())
    
    template_data = {
        "cost_types": await storage.load_cost_types(),
        "current_costs": await storage.load_costs()
    }
    
    html = await render('usage', template_data)
    return HTMLResponse(html)

@router.post("/api/admin/usage/costs")
async def update_costs(request: Request):
    """Update cost configuration"""
    try:
        storage = UsageStorage(get_base_path())
        data = await request.json()
        
        plugin_id = data.get('plugin_id')
        cost_type_id = data.get('cost_type_id')
        unit_cost = float(data.get('unit_cost', 0))
        model_id = data.get('model_id')
        
        if not all([plugin_id, cost_type_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        await storage.save_cost(plugin_id, cost_type_id, unit_cost, model_id)
        return JSONResponse({"status": "success"})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/usage/report/{username}")
async def get_user_report(
    request: Request,
    username: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get usage report for a specific user"""
    try:
        storage = UsageStorage(get_base_path())
        report = UsageReport(storage)
        
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        report_data = await report.get_user_report(username, start, end)
        return JSONResponse(report_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/usage/summary/{username}")
async def get_user_summary(
    request: Request,
    username: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get cost summary for a specific user"""
    try:
        storage = UsageStorage(get_base_path())
        report = UsageReport(storage)
        
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        summary = await report.get_cost_summary(username, start, end)
        return JSONResponse(summary)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/usage/daily/{username}")
async def get_user_daily(
    request: Request,
    username: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get daily cost breakdown for a specific user"""
    try:
        storage = UsageStorage(get_base_path())
        report = UsageReport(storage)
        
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        daily_costs = await report.get_daily_costs(username, start, end)
        return JSONResponse(daily_costs)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
