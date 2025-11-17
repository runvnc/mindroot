import asyncio
from typing import Dict
from services import init_provider, send_email, check_emails, mark_as_processed
import traceback
import os
from datetime import datetime, timedelta
TEST_CONFIG = {'smtp_server': 'smtp.gmail.com', 'smtp_port': 587, 'use_tls': True, 'email': 'runvnc@gmail.com', 'password': os.environ.get('GMAIL_APP_PASSWORD'), 'imap_server': 'imap.gmail.com', 'imap_port': 993, 'batch_size': 50, 'max_messages': 200}

async def test_send_email():
    """Test sending a simple email"""
    result = await send_email(config=TEST_CONFIG, to='ithkuil@gmail.com', subject='Test Email', body='This is a test email.', headers={'X-Test': 'true'})
    return result

async def test_check_emails_with_pagination():
    """Test checking emails with pagination"""
    six_months_ago = datetime.now() - timedelta(days=180)
    next_id = None
    batch_count = 0
    total_messages = 0
    while True:
        result = await check_emails(config=TEST_CONFIG, folder='INBOX', criteria={'unread_only': True, 'since_date': six_months_ago}, batch_size=50, start_id=next_id)
        if not result['success']:
            break
        messages = result['messages']
        pagination = result['pagination']
        total_messages += len(messages)
        if pagination:
            if not pagination['has_more']:
                break
            next_id = pagination['next_id']
            batch_count += 1
            if batch_count >= 4:
                break
        else:
            break
    return result

async def test_mark_processed():
    """Test marking emails as processed"""
    check_result = await check_emails(config=TEST_CONFIG, criteria={'unread_only': True, 'since_date': datetime.now() - timedelta(days=180)}, batch_size=1)
    if check_result['success'] and check_result['messages']:
        message_ids = [check_result['messages'][0]['id']]
        result = await mark_as_processed(config=TEST_CONFIG, message_ids=message_ids)
        return result
    else:
        return {'success': False, 'error': 'No messages to mark'}

async def test_reply():
    """Test sending a reply to an email"""
    check_result = await check_emails(config=TEST_CONFIG, folder='INBOX', criteria={'since_date': datetime.now() - timedelta(days=180)}, batch_size=1)
    if check_result['success'] and check_result['messages']:
        original_message = check_result['messages'][0]
        result = await send_email(config=TEST_CONFIG, to=original_message['from'], subject=original_message['subject'], body='This is a test reply.', reply_to_message=original_message, headers={'X-Test-Reply': 'true'})
        return result
    else:
        return {'success': False, 'error': 'No messages to reply to'}

async def run_tests():
    """Run all tests"""
    try:
        await init_provider(TEST_CONFIG)
        await test_check_emails_with_pagination()
    except Exception as e:
        trace = traceback.format_exc()
if __name__ == '__main__':
    asyncio.run(run_tests())