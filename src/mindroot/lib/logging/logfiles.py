import os
import json
import sys
from datetime import datetime, timedelta
from loguru import logger
if not os.path.exists('logs'):
    os.makedirs('logs')
logger.remove()
logger.add(sys.stderr, format='{time} | {level} | {function} | {message}', level='INFO')

def json_sink(message):
    record = message.record
    log_entry = {'time': record['time'].isoformat(), 'level': record['level'].name, 'function': record['function'], 'message': record['message'], 'extra': record['extra']}
    write_log(log_entry)
logger.info('This is a test log message')
logger.add(json_sink, level='DEBUG')

def generate_file_name(timestamp):
    return f"logs/log_{timestamp.strftime('%Y-%m-%d_%H')}.json"

def get_log_files(start_time, end_time):
    files_to_read = []
    current_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)
    while current_time <= end_time:
        file_name = generate_file_name(current_time)
        if os.path.exists(file_name):
            files_to_read.append(file_name)
        current_time += timedelta(hours=1)
    return files_to_read

async def get_logs(start_time, end_time, search_str=None, exclude_str=None, limit=30000, cursor=None):
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)
    files = get_log_files(start_time, end_time)
    logs = []
    next_cursor = None
    for file in files:
        with open(file, 'r') as f:
            for line in f:
                if search_str is not None and search_str not in line:
                    continue
                if exclude_str is not None and exclude_str in line:
                    continue
                log_entry = json.loads(line)
                log_time = datetime.fromisoformat(log_entry['time']).replace(tzinfo=None)
                if cursor and log_time <= cursor.replace(tzinfo=None):
                    continue
                if start_time <= log_time <= end_time:
                    logs.append(log_entry)
                if len(logs) == limit:
                    next_cursor = log_time
                    break
        if next_cursor:
            break
    return (logs, next_cursor)

def write_log(log_entry):
    timestamp = datetime.fromisoformat(log_entry['time'])
    file_name = generate_file_name(timestamp)
    with open(file_name, 'a') as f:
        json.dump(log_entry, f)
        f.write('\n')