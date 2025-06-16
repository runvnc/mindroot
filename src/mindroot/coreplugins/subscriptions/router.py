from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from lib.templates import render
from lib.route_decorators import requires_role
from typing import Dict, List, Optional, Any
from loguru import logger
import traceback
from decimal import Decimal
import json

from lib.providers.services import service_manager

from .mod import (
    create_subscription_plan,
    get_subscription_plans,
    get_subscription_plan,
    update_subscription_plan,
    deactivate_subscription_plan,
    activate_subscription_plan,
    get_available_features,
    create_plan_feature,
    update_plan_feature,
    deactivate_plan_feature,
    activate_plan_feature,
    get_page_templates,
    create_page_template,
    update_page_template,
    set_default_template,
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

# Admin API routes - Plans

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
        plan = await update_subscription_plan(plan_id, data, context=request)
        return JSONResponse({"status": "success", "plan": plan})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating plan: {e}")
        raise SERVER_ERROR

@router_admin.delete("/plans/{plan_id}")
async def api_deactivate_plan(plan_id: str, request: Request):
    """Deactivate a subscription plan"""
    try:
        result = await deactivate_subscription_plan(plan_id, context=request)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating plan: {e}")
        raise SERVER_ERROR

@router_admin.post("/plans/{plan_id}/activate")
async def api_activate_plan(plan_id: str, request: Request):
    """Activate a subscription plan"""
    try:
        result = await activate_subscription_plan(plan_id, context=request)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating plan: {e}")
        raise SERVER_ERROR

# Admin API routes - Features

@router_admin.get("/features/list")
async def api_get_features(request: Request, active_only: bool = False):
    """Get all plan features"""
    try:
        features = await get_available_features(active_only, context=request)
        return JSONResponse({"status": "success", "features": features})
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        raise SERVER_ERROR

@router_admin.post("/features")
async def api_create_feature(request: Request):
    """Create a new plan feature"""
    try:
        data = await request.json()
        feature = await create_plan_feature(data, context=request)
        return JSONResponse({"status": "success", "feature": feature})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating feature: {e}")
        raise SERVER_ERROR

@router_admin.put("/features/{feature_id}")
async def api_update_feature(feature_id: str, request: Request):
    """Update an existing plan feature"""
    try:
        data = await request.json()
        feature = await update_plan_feature(feature_id, data, context=request)
        return JSONResponse({"status": "success", "feature": feature})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating feature: {e}")
        raise SERVER_ERROR

@router_admin.post("/features/{feature_id}/deactivate")
async def api_deactivate_feature(feature_id: str, request: Request):
    """Deactivate a plan feature"""
    try:
        result = await deactivate_plan_feature(feature_id, context=request)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating feature: {e}")
        raise SERVER_ERROR

@router_admin.post("/features/{feature_id}/activate")
async def api_activate_feature(feature_id: str, request: Request):
    """Activate a plan feature"""
    try:
        result = await activate_plan_feature(feature_id, context=request)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating feature: {e}")
        raise SERVER_ERROR

# Admin API routes - Templates

@router_admin.get("/templates/list")
async def api_get_templates(request: Request):
    """Get all page templates"""
    try:
        templates = await get_page_templates(context=request)
        return JSONResponse({"status": "success", "templates": templates})
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise SERVER_ERROR

@router_admin.post("/templates")
async def api_create_template(request: Request):
    """Create a new page template"""
    try:
        data = await request.json()
        template = await create_page_template(data, context=request)
        return JSONResponse({"status": "success", "template": template})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise SERVER_ERROR

@router_admin.put("/templates/{template_id}")
async def api_update_template(template_id: str, request: Request):
    """Update an existing page template"""
    try:
        data = await request.json()
        template = await update_page_template(template_id, data, context=request)
        return JSONResponse({"status": "success", "template": template})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise SERVER_ERROR

@router_admin.post("/templates/{template_id}/set-default")
async def api_set_default_template(template_id: str, request: Request):
    """Set a template as the default"""
    try:
        result = await set_default_template(template_id, context=request)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting default template: {e}")
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
        print("checkout")
        if not request.state.user:
            print("Unauthorized")
            raise UNAUTHORIZED
            
        username = request.state.user.username
        
        # Get plan details
        plan = await get_subscription_plan(plan_id, context=request)
        if not plan:
            print("could not find plan",plan_id)
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

@router_public.get("/page", response_class=HTMLResponse)
async def subscription_page(request: Request):
    """Public subscription page"""
    try:
        # Get active plans
        plans = await get_subscription_plans(active_only=True, context=request)
        
        # Get user's subscriptions if logged in
        user_subscriptions = []
        if request.state.user:
            user_subscriptions = await get_user_subscriptions(request.state.user.username, context=request)
        
        template_data = {
            "plans": plans,
            "user_subscriptions": user_subscriptions
        }
        
        html = await render('subscription_page', template_data)
        return HTMLResponse(html)
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Error rendering subscription page: {e}\n\n {trace}")
        raise SERVER_ERROR

# Combine all routers
router = APIRouter()
router.include_router(router_admin)
router.include_router(router_public)
