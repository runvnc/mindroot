from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import date, datetime
from typing import Optional, Dict, Any
from lib.templates import render
from loguru import logger
from .models import CreditTransaction
from lib.route_decorators import requires_role

import traceback

from .mod import (
    allocate_credits,
    get_credit_report,
    estimate_credits,
    get_credit_ratios,
    set_credit_ratio
)

# Define common error responses
INVALID_REQUEST = HTTPException(status_code=400, detail="Invalid request parameters")
INSUFFICIENT_CREDITS = HTTPException(status_code=402, detail="Insufficient credits")
SERVER_ERROR = HTTPException(status_code=500, detail="Internal server error")

router = APIRouter(dependencies=[requires_role('admin')])

@router.get("/admin/credits")
async def credits_admin(request: Request):
    """Admin interface for credit management"""
    try:
        credit_ratios = await get_credit_ratios(context=request)
        template_data = {
            "credit_ratios": credit_ratios
        }
        
        html = await render('credits', template_data)
        return HTMLResponse(html)
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Error in credits_admin: {e}\n\n{trace}")
        # we need to fix this now to give the actual error message and stack trace
        raise HTTPException(status_code=500, detail="Internal server error\n\n"+trace)

@router.get("/admin/credits/ratios")
async def credits_ratio_admin(request: Request):
    """Admin interface for credit ratio configuration"""
    try:
        credit_ratios = await get_credit_ratios(context=request)
        template_data = {
            "credit_ratios": credit_ratios
        }
        
        html = await render('credit_ratios', template_data)
        return HTMLResponse(html)
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Error in credits_admin: {e}\n\n{trace}")
        # we need to fix this now to give the actual error message and stack trace
        raise HTTPException(status_code=500, detail="Internal server error\n\n"+trace)

@router.post("/api/admin/credits/allocate")
async def api_allocate_credits(request: Request):
    """Allocate credits to a user
    
    Request body:
    {
        "username": str,
        "amount": float,
        "source": str,
        "reference_id": str,
        "metadata": dict (optional)
    }
    """
    try:
        data = await request.json()
        username = data.get('username')
        try:
            amount = float(data.get('amount', 0))
        except (TypeError, ValueError):
            raise INVALID_REQUEST
            
        source = data.get('source', 'admin_grant')
        reference_id = data.get('reference_id')
        metadata = data.get('metadata', {})
        
        if not all([username, amount > 0, reference_id]):
            raise INVALID_REQUEST
        
        new_balance = await allocate_credits(
            username, amount, source, reference_id, metadata,
            context=request
        )
        
        return JSONResponse({
            "status": "success",
            "new_balance": new_balance
        })
        
    except Exception as e:
        raise SERVER_ERROR

@router.post("/api/admin/credits/ratios")
async def api_update_ratio(request: Request):
    """Update credit ratio configuration
    
    Request body:
    {
        "ratio": float,
        "plugin_id": str (optional),
        "cost_type_id": str (optional),
        "model_id": str (optional)
    }
    """
    try:
        data = await request.json()
        try:
            ratio = float(data.get('ratio', 0))
        except (TypeError, ValueError):
            raise INVALID_REQUEST
            
        plugin_id = data.get('plugin_id')
        cost_type_id = data.get('cost_type_id')
        model_id = data.get('model_id')
        
        if ratio <= 0:
            raise INVALID_REQUEST
        
        await set_credit_ratio(
            ratio, plugin_id, cost_type_id, model_id,
            context=request
        )
        
        return JSONResponse({"status": "success"})
        
    except ValueError as e:
        raise INVALID_REQUEST
    except Exception as e:
        raise SERVER_ERROR

@router.get("/api/admin/credits/report/{username}")
async def api_credit_report(username: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          request: Request = None):
    """Get credit report for a user
    
    Path parameters:
        username: str - Username to get report for
    
    Query parameters:
        start_date: Optional[str] - Start date in YYYY-MM-DD format
        end_date: Optional[str] - End date in YYYY-MM-DD format
    """
    try:
        report = await get_credit_report(
            username, start_date, end_date,
            context=request
        )
        return JSONResponse(report)
    except Exception as e:
        raise SERVER_ERROR

@router.get("/api/admin/credits/estimate")
async def api_estimate_credits(plugin_id: str,
                             cost_type_id: str,
                             estimated_cost: float,
                             model_id: Optional[str] = None,
                             request: Request = None):
    """Estimate credits needed for an operation
    
    Query parameters:
        plugin_id: str - Plugin identifier
        cost_type_id: str - Cost type identifier
        estimated_cost: float - Estimated cost in base currency
        model_id: Optional[str] - Model identifier
    """
    try:
        if not all([plugin_id, cost_type_id]) or estimated_cost <= 0:
            raise INVALID_REQUEST
            
        estimate = await estimate_credits(
            plugin_id, cost_type_id, estimated_cost, model_id,
            context=request
        )
        return JSONResponse(estimate)
    except Exception as e:
        raise SERVER_ERROR
