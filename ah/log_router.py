from loguru import logger
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from datetime import datetime
from .logfiles import get_logs

router = APIRouter()

@router.get("/logs", response_class=HTMLResponse)
async def get_logs_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
            h1 { color: #333; }
            .instructions { background-color: #f4f4f4; padding: 15px; border-radius: 5px; }
            .browser-instructions { margin-top: 20px; }
            .browser-instructions h3 { margin-bottom: 5px; }
            .browser-instructions ul { margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>Log Viewer</h1>
        <div class="instructions">
            <p>To view logs, you need to open your browser's Developer Console. Here's how to do it in different browsers:</p>
            
            <div class="browser-instructions">
                <h3>Chrome / Edge:</h3>
                <ul>
                    <li>Windows/Linux: Press Ctrl + Shift + J</li>
                    <li>Mac: Press Cmd + Option + J</li>
                    <li>Or go to Menu > More Tools > Developer Tools, then click on "Console" tab</li>
                </ul>
            </div>
            
            <div class="browser-instructions">
                <h3>Firefox:</h3>
                <ul>
                    <li>Windows/Linux: Press Ctrl + Shift + K</li>
                    <li>Mac: Press Cmd + Option + K</li>
                    <li>Or go to Menu > Web Developer > Web Console</li>
                </ul>
            </div>
            
            <div class="browser-instructions">
                <h3>Safari:</h3>
                <ul>
                    <li>Press Cmd + Option + C</li>
                    <li>Or go to Develop > Show JavaScript Console (you may need to enable the Develop menu in Safari preferences)</li>
                </ul>
            </div>
        </div>
        
        <script>
            async function fetchLogs() {
                const end = new Date();
                const start = new Date(end.getTime() - 10 * 60 * 1000);  // 10 minutes ago
                const response = await fetch(`/api/logs?start=${start.toISOString()}&end=${end.toISOString()}`);
                const logs = await response.json();
                console.log(logs);
            }
            fetchLogs();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/api/logs")
async def api_logs(
    start: str = Query(..., description="Start time (ISO format)"),
    end: str = Query(..., description="End time (ISO format)"),
    limit: int = Query(1000, description="Maximum number of logs to return"),
    cursor: str = Query(None, description="Cursor for pagination")
):
    start_time = datetime.fromisoformat(start)
    end_time = datetime.fromisoformat(end)
    cursor_time = datetime.fromisoformat(cursor) if cursor else None

    logs, next_cursor = await get_logs(start_time, end_time, limit, cursor_time)

    return {
        "logs": logs,
        "next_cursor": next_cursor.isoformat() if next_cursor else None
    }
