"""OAuth callback router for MCP servers.

This router contains public routes that do not require authentication,
as external OAuth providers need to be able to redirect to these endpoints.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from lib.route_decorators import public_route

# Create router without dependencies - routes will be public
router = APIRouter()

@router.get("/mcp_oauth_cb")
@public_route()
async def mcp_oauth_callback(request: Request):
    """Handle OAuth callback for MCP servers.
    
    This endpoint must be publicly accessible as external OAuth providers
    will redirect to it without any authentication.
    """
    try:
        # Get query parameters
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')
        
        if error:
            # OAuth error occurred - avoid f-string issues
            error_html = (
                "<html><body>"
                "<h2>OAuth Authorization Failed</h2>"
                f"<p>Error: {error}</p>"
                "<p>You can close this window.</p>"
                "<script>window.close();</script>"
                "</body></html>"
            )
            return HTMLResponse(error_html)
        
        if code:
            # Success - show completion page
            state_value = state or ""
            # Build HTML without f-string to avoid escaping issues
            success_html = (
                "<html><body>"
                "<h2>OAuth Authorization Successful</h2>"
                "<p>Authorization code received. You can close this window.</p>"
                "<script>"
                "if (window.opener) {"
                "window.opener.postMessage({"
                "type: 'oauth_callback',"
                f"code: '{code}',"
                f"state: '{state_value}'"
                "}, '*');"
                "}"
                "setTimeout(() => window.close(), 2000);"
                "</script>"
                "</body></html>"
            )
            return HTMLResponse(success_html)
        
        # No code or error - invalid callback
        invalid_html = (
            "<html><body>"
            "<h2>Invalid OAuth Callback</h2>"
            "<p>Missing authorization code or error parameter.</p>"
            "<p>You can close this window.</p>"
            "<script>window.close();</script>"
            "</body></html>"
        )
        return HTMLResponse(invalid_html)
        
    except Exception as e:
        # Error handling - escape special characters
        error_message = str(e).replace('"', '&quot;').replace("'", "&#39;")
        error_html = (
            "<html><body>"
            "<h2>OAuth Callback Error</h2>"
            f"<p>An error occurred processing the OAuth callback: {error_message}</p>"
            "<p>You can close this window.</p>"
            "<script>window.close();</script>"
            "</body></html>"
        )
        return HTMLResponse(error_html)
