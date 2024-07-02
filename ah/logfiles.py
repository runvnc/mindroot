import os
import json
import sys
from datetime import datetime, timedelta
from loguru import logger

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

def generate_file_name(timestamp):
    return f"logs/log_{timestamp.strftime('%Y-%m-%d_%H')}.json"

def get_log_files(start_time, end_time):
    files_to_read = []
    current_time = start_time
    while current_time <= end_time:
        file_name = generate_file_name(current_time)
        if os.path.exists(file_name):
            files_to_read.append(file_name)
        current_time += timedelta(hours=1)
    return files_to_read

async def get_logs(start_time, end_time, limit=1000, cursor=None):
    files = get_log_files(start_time, end_time)
    logs = []
    next_cursor = None

    for file in files:
        with open(file, 'r') as f:
            for line in f:
                log_entry = json.loads(line)
                log_time = datetime.fromisoformat(log_entry['time'])
                
                if cursor and log_time <= cursor:
                    continue
                
                if start_time <= log_time <= end_time:
                    logs.append(log_entry)
                    
                if len(logs) == limit:
                    next_cursor = log_time
                    break
        
        if next_cursor:
            break

    return logs, next_cursor

def write_log(log_entry):
    timestamp = datetime.fromisoformat(log_entry['time'])
    file_name = generate_file_name(timestamp)
    
    with open(file_name, 'a') as f:
        json.dump(log_entry, f)
        f.write('\n')
