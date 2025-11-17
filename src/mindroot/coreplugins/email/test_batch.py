import asyncio
from typing import Dict
from services import init_provider, check_emails
import traceback
import os
from datetime import datetime, timedelta
TEST_CONFIG = {'smtp_server': 'smtp.gmail.com', 'smtp_port': 587, 'use_tls': True, 'email': 'runvnc@gmail.com', 'password': os.environ.get('GMAIL_APP_PASSWORD'), 'imap_server': 'imap.gmail.com', 'imap_port': 993, 'batch_size': 50, 'max_messages': 1000}

async def test_batch_processing():
    """Test processing recent messages in batches"""
    two_weeks_ago = datetime.now() - timedelta(days=14)
    next_id = None
    batch_count = 0
    total_messages = 0
    processed_ids = set()
    while True:
        result = await check_emails(config=TEST_CONFIG, folder='INBOX', criteria={'since_date': two_weeks_ago}, batch_size=50, start_id=next_id)
        if not result['success']:
            break
        messages = result['messages']
        pagination = result['pagination']
        current_ids = set((msg['id'] for msg in messages))
        duplicates = current_ids.intersection(processed_ids)
        processed_ids.update(current_ids)
        total_messages += len(messages)
        if pagination:
            if not pagination['has_more']:
                break
            next_id = pagination['next_id']
            batch_count += 1
            if total_messages >= TEST_CONFIG['max_messages']:
                break
        else:
            break
    return result

async def run_test():
    """Run the batch processing test"""
    try:
        await init_provider(TEST_CONFIG)
        await test_batch_processing()
    except Exception as e:
        trace = traceback.format_exc()
if __name__ == '__main__':
    asyncio.run(run_test())