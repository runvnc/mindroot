from loguru import logger
import sys
import json
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from .logfiles import get_logs, write_log

# Configure loguru
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="{time} | {level} | {message}", level="INFO")

# Custom sink for JSON logging
def json_sink(message):
    record = message.record
    log_entry = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "extra": record["extra"],
    }
    write_log(log_entry)

logger.add(json_sink, level="DEBUG")

router = APIRouter()

@router.get("/logs", response_class=HTMLResponse)
async def get_logs_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Viewer</title>
    </head>
    <body>
        <h1>Log Viewer</h1>
        <p>Open the browser console (F12) to view logs.</p>
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
