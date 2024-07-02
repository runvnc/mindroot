from loguru import logger
import sys
import json
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

# Configure loguru
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="{time} | {level} | {message}", level="INFO")
logger.add("logs/file_{time}.log", rotation="500 MB", level="DEBUG", serialize=True)

# Custom sink for JSON logging
def json_sink(message):
    record = message.record
    log_entry = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "extra": record["extra"],
    }
    print(json.dumps(log_entry))

logger.add(json_sink, level="INFO")

router = APIRouter()

@router.get("/logs", response_class=HTMLResponse)
async def get_logs():
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
                const response = await fetch('/api/logs');
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
async def api_logs():
    # This is a placeholder. You'll need to implement log reading logic here.
    # For now, we'll return a sample log entry
    return [
        {"time": "2023-06-01T12:00:00", "level": "INFO", "message": "Sample log entry"},
        {"time": "2023-06-01T12:01:00", "level": "DEBUG", "message": "Another log entry"}
    ]
