from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import JSONResponse
from lib.route_decorators import requires_role
from .mod import scan_env_vars, update_env_var

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

@router.get("/env_vars/scan")
async def get_env_vars(request: Request):
    """Scan all enabled plugins for environment variable references."""
    try:
        results = await scan_env_vars()
        return JSONResponse({
            "success": True,
            "data": results
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/env_vars/update")
async def update_environment_var(
    request: Request,
    var_name: str = Body(...),
    var_value: str = Body(...)
):
    """Update an environment variable."""
    try:
        result = await update_env_var(var_name, var_value)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
