from loguru import logger
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from .logfiles import get_logs

router = APIRouter()

@router.get("/logs", response_class=HTMLResponse)
async def get_logs_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Viewer 0.5</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
            h1 { color: #333; }
            .instructions { background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .browser-instructions { margin-top: 20px; }
            .browser-instructions h3 { margin-bottom: 5px; }
            .browser-instructions ul { margin-top: 5px; }
            form { margin-bottom: 20px; }
            label { display: inline-block; margin-right: 10px; }
            input[type="datetime-local"] { margin-right: 20px; }
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
        
        <form id="logForm">
            <label for="startTime">Start Time:</label>
            <input type="datetime-local" id="startTime" name="startTime">
            
            <label for="endTime">End Time:</label>
            <input type="datetime-local" id="endTime" name="endTime">
            
            <label for="presentTime">
                <input type="checkbox" id="presentTime" name="presentTime" checked>
                Use Present Time
            </label>

            <label for="searchStr">Search:
                <input type="text" id="searchStr" name="search" placeholder="Search string">
            </label>
            
            <label for="searchStr">Exclude:
                <input type="text" id="excludeStr" name="exclude" placeholder="Exclude string">
            </label>            
            <button type="submit">Fetch Logs</button>
        </form>
        
        <script>
            function setDefaultTimes() {
                const now = new Date();
                const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);
                
                document.getElementById('startTime').value = tenMinutesAgo.toString() ;//toISOString().slice(0, 16);
                document.getElementById('endTime').value = now.toString(); //
            }

            function toggleEndTime() {
                const endTimeInput = document.getElementById('endTime');
                endTimeInput.disabled = document.getElementById('presentTime').checked;
            }

            document.getElementById('presentTime').addEventListener('change', toggleEndTime);

            document.getElementById('logForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                await fetchLogs();
            });

            async function fetchLogs() {
                const startTime = document.getElementById('startTime').value;
                let endTime = document.getElementById('endTime').value;
                
                if (document.getElementById('presentTime').checked) {
                    endTime = new Date().toISOString();
                }
                let searchStr = null;
                if (document.getElementById('searchStr').value) {
                    searchStr = document.getElementById('searchStr').value;
                }

                let excludeStr = null;
                if (document.getElementById('excludeStr').value) {
                    excludeStr = document.getElementById('excludeStr').value;
                }

                const response = await fetch(`/api/logs?start=${startTime}&end=${endTime}&search_str=${searchStr}&exclude_str=${excludeStr}`)
                const logs = await response.json();
                console.log(logs);
            }

            setDefaultTimes();
            toggleEndTime();
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
    search_str: str = Query(None, description="Search string"),
     exclude_str: str = Query(None, text="Exclude text"),
    cursor: str = Query(None, description="Cursor for pagination")
):
    start_time = datetime.fromisoformat(start)
    end_time = datetime.fromisoformat(end)
    cursor_time = datetime.fromisoformat(cursor) if cursor else None
    search_str = search_str.strip() if search_str else None
    exclude_str = exclude_str.strip() if exclude_str else None
    if search_str == 'null':
        search_str = None

    logs, next_cursor = await get_logs(start_time, end_time, search_str, exclude_str, limit, cursor_time)

    return {
        "logs": logs,
        "next_cursor": next_cursor.isoformat() if next_cursor else None
    }
