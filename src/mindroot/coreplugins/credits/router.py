from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import date
from typing import Optional
from lib.templates import render
from .models import CreditTransaction
from .ledger import CreditLedger, InsufficientCreditsError
from .mod import (_ledger, _ratio_config, allocate_credits, 
                 get_credit_report, estimate_credits)

router = APIRouter()

@router.get("/admin/credits")
async def credits_admin(request: Request):
    """Admin interface for credit management"""
    template_data = {
        "credit_ratios": _ratio_config.get_config()
    }
    
    html = await render('admin/credits.jinja2', template_data)
    return HTMLResponse(html)

@router.get("/admin/credits/ratios")
async def credits_ratio_admin(request: Request):
    """Admin interface for credit ratio configuration"""
    template_data = {
        "credit_ratios": _ratio_config.get_config()
    }
    
    html = await render('admin/credit_ratios.jinja2', template_data)
    return HTMLResponse(html)

@router.post("/api/admin/credits/allocate")
async def api_allocate_credits(request: Request):
    """Allocate credits to a user"""
    try:
        data = await request.json()
        username = data.get('username')
        amount = float(data.get('amount', 0))
        source = data.get('source', 'admin_grant')
        reference_id = data.get('reference_id')
        metadata = data.get('metadata', {})
        
        if not all([username, amount > 0, reference_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        new_balance = await allocate_credits(
            username, amount, source, reference_id, metadata
        )
        
        return JSONResponse({
            "status": "success",
            "new_balance": new_balance
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/admin/credits/ratios")
async def api_update_ratio(request: Request):
    """Update credit ratio configuration"""
    try:
        data = await request.json()
        ratio = float(data.get('ratio', 0))
        plugin_id = data.get('plugin_id')
        cost_type_id = data.get('cost_type_id')
        model_id = data.get('model_id')
        
        if ratio <= 0:
            raise HTTPException(status_code=400, detail="Ratio must be positive")
        
        _ratio_config.set_ratio(ratio, plugin_id, cost_type_id, model_id)
        
        return JSONResponse({"status": "success"})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/credits/report/{username}")
async def api_credit_report(username: str,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None):
    """Get credit report for a user"""
    try:
        report = await get_credit_report(username, start_date, end_date)
        return JSONResponse(report)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/admin/credits/estimate")
async def api_estimate_credits(plugin_id: str,
                              cost_type_id: str,
                              estimated_cost: float,
                              model_id: Optional[str] = None):
    """Estimate credits needed for an operation"""
    try:
        estimate = await estimate_credits(
            plugin_id, cost_type_id, estimated_cost, model_id
        )
        return JSONResponse(estimate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
