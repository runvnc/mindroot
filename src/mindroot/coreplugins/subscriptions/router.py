from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from lib.templates import render
from lib.route_decorators import requires_role
from typing import Dict, List, Optional, Any
from loguru import logger
import traceback
from decimal import Decimal

from lib.providers.services import service_manager

from .mod import (
    create_subscription_plan,
    get_subscription_plans,
    get_subscription_plan,
    process_subscription_event,
    get_user_subscriptions,
    cancel_subscription
)

# Define common error responses
INVALID_REQUEST = HTTPException(status_code=400, detail="Invalid request parameters")
UNAUTHORIZED = HTTPException(status_code=401, detail="Unauthorized")
NOT_FOUND = HTTPException(status_code=404, detail="Resource not found")
SERVER_ERROR = HTTPException(status_code=500, detail="Internal server error")

# Admin routes
router_admin = APIRouter(dependencies=[requires_role('admin')], prefix="/admin/subscriptions")

# Public routes
router_public = APIRouter(prefix="/subscriptions")

# Admin UI routes

@router_admin.get("", response_class=HTMLResponse)
async def subscriptions_admin(request: Request):
    """Admin interface for subscription management"""
    try:
        plans = await get_subscription_plans(context=request)
        template_data = {
            "plans": plans
        }
        
        html = await render('subscriptions_admin', template_data)
        return HTMLResponse(html)
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Error in subscriptions_admin: {e}\n\n{trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error\n\n{trace}")

# Admin API routes

@router_admin.post("/plans")
async def api_create_plan(request: Request):
    """Create a new subscription plan"""
    try:
        data = await request.json()
        plan = await create_subscription_plan(data, context=request)
        return JSONResponse({"status": "success", "plan": plan})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise SERVER_ERROR

@router_admin.get("/plans")
async def api_get_all_plans(request: Request, active_only: bool = True):
    """Get all subscription plans"""
    try:
        plans = await get_subscription_plans(active_only, context=request)
        return JSONResponse({"status": "success", "plans": plans})
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        raise SERVER_ERROR

@router_admin.put("/plans/{plan_id}")
async def api_update_plan(plan_id: str, request: Request):
    """Update an existing subscription plan"""
    try:
        data = await request.json()
        # This service needs to be implemented
        # plan = await update_subscription_plan(plan_id, data, context=request)
        # For now, we'll return a placeholder
        return JSONResponse({"status": "success", "message": "Plan updated"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating plan: {e}")
        raise SERVER_ERROR

@router_admin.delete("/plans/{plan_id}")
async def api_deactivate_plan(plan_id: str, request: Request):
    """Deactivate a subscription plan"""
    try:
        # This service needs to be implemented
        # await deactivate_subscription_plan(plan_id, context=request)
        # For now, we'll return a placeholder
        return JSONResponse({"status": "success", "message": "Plan deactivated"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating plan: {e}")
        raise SERVER_ERROR

# Public API routes

@router_public.get("/plans")
async def api_get_plans(request: Request):
    """Get available subscription plans"""
    try:
        plans = await get_subscription_plans(active_only=True, context=request)
        return JSONResponse({"status": "success", "plans": plans})
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        raise SERVER_ERROR

@router_public.post("/checkout/{plan_id}")
async def api_create_checkout(plan_id: str, 
                            request: Request, 
                            provider: str = Query('stripe')):
    """Create checkout session for subscription"""
    try:
        if not request.state.user:
            raise UNAUTHORIZED
            
        username = request.state.user.username
        
        # Get plan details
        plan = await get_subscription_plan(plan_id, context=request)
        if not plan:
            raise NOT_FOUND
        
        # Call provider-specific checkout service
        # The service name is 'subscription_checkout' for all providers
        try:
            checkout_url = await service_manager.subscription_checkout(
                user_id=username,
                plan_name=plan['name'],
                amount=Decimal(str(plan['price'])),
                interval=plan['interval'],
                currency=plan['currency'],
                metadata={
                    'plan_id': plan['plan_id'],
                    'credits_per_cycle': plan['credits_per_cycle'],
                    'source': 'subscription_plugin'
                }
            )
            
            return JSONResponse({"status": "success", "url": checkout_url})
        except AttributeError:
            logger.error(f"Payment provider '{provider}' not available")
            raise HTTPException(status_code=400, detail=f"Payment provider '{provider}' not available")
        except Exception as e:
            logger.error(f"Error creating checkout: {e}")
            raise SERVER_ERROR
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise SERVER_ERROR

@router_public.get("/my")
async def api_get_my_subscriptions(request: Request):
    """Get current user's subscriptions"""
    try:
        if not request.state.user:
            raise UNAUTHORIZED
            
        username = request.state.user.username
        subscriptions = await get_user_subscriptions(username, context=request)
        
        return JSONResponse({"status": "success", "subscriptions": subscriptions})
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise SERVER_ERROR

@router_public.post("/cancel/{subscription_id}")
async def api_cancel_subscription(subscription_id: str, request: Request, at_period_end: bool = True):
    """Cancel a subscription"""
    try:
        if not request.state.user:
            raise UNAUTHORIZED
            
        # Get subscription to check ownership
        subscriptions = await get_user_subscriptions(request.state.user.username, context=request)
        subscription_ids = [sub['subscription_id'] for sub in subscriptions]
        
        # Only allow cancellation if user owns the subscription or is admin
        if subscription_id not in subscription_ids and 'admin' not in request.state.user.roles:
            raise UNAUTHORIZED
        
        result = await cancel_subscription(subscription_id, at_period_end, context=request)
        
        return JSONResponse({"status": "success", "subscription": result})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise SERVER_ERROR

# Combine all routers
router = APIRouter()
router.include_router(router_admin)
router.include_router(router_public)
