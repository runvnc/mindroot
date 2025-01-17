import asyncio
from typing import Dict
from services import init_provider, send_email, check_emails, mark_as_processed
import traceback
import os
from datetime import datetime, timedelta

# Test configuration
TEST_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True,
    "email": "runvnc@gmail.com",  # Replace with test email
    "password": os.environ.get("GMAIL_APP_PASSWORD"),
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "batch_size": 50,  # Process 50 messages at a time
    "max_messages": 200  # Maximum total messages to process
}

async def test_send_email():
    """Test sending a simple email"""
    print("\nTesting send_email...")
    
    result = await send_email(
        config=TEST_CONFIG,
        to="ithkuil@gmail.com",  # Replace with test recipient
        subject="Test Email",
        body="This is a test email.",
        headers={"X-Test": "true"}
    )
    
    print(f"Send result: {result}")
    return result

async def test_check_emails_with_pagination():
    """Test checking emails with pagination"""
    print("\nTesting check_emails with pagination...")
    
    # Calculate date 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    next_id = None
    batch_count = 0
    total_messages = 0
    
    while True:
        print(f"\nFetching batch {batch_count + 1}...")
        result = await check_emails(
            config=TEST_CONFIG,
            folder="INBOX",
            criteria={
                "unread_only": True,
                "since_date": six_months_ago
            },
            batch_size=50,
            start_id=next_id
        )
        
        if not result["success"]:
            print(f"Error: {result['error']}")
            break
            
        messages = result["messages"]
        pagination = result["pagination"]
        
        print(f"Fetched {len(messages)} messages")
        total_messages += len(messages)
        
        # Print first few messages in batch
        for msg in messages[:3]:
            print(f"\nFrom: {msg['from']}")
            print(f"Subject: {msg['subject']}")
            print(f"Date: {msg['date']}")
        
        if pagination:
            print(f"\nPagination info:")
            print(f"Total messages available: {pagination['total_messages']}")
            print(f"Has more: {pagination['has_more']}")
            
            if not pagination['has_more']:
                break
                
            next_id = pagination['next_id']
            batch_count += 1
            
            # Optional: limit number of batches for testing
            if batch_count >= 4:  # Will process up to 200 messages (4 batches * 50 messages)
                print("\nReached maximum test batches")
                break
        else:
            break
    
    print(f"\nTotal messages processed: {total_messages}")
    return result

async def test_mark_processed():
    """Test marking emails as processed"""
    print("\nTesting mark_as_processed...")
    
    # Get one batch of unread messages
    check_result = await check_emails(
        config=TEST_CONFIG,
        criteria={
            "unread_only": True,
            "since_date": datetime.now() - timedelta(days=180)
        },
        batch_size=1  # Just get one message
    )
    
    if check_result["success"] and check_result["messages"]:
        # Mark first message as processed
        message_ids = [check_result["messages"][0]["id"]]
        result = await mark_as_processed(
            config=TEST_CONFIG,
            message_ids=message_ids
        )
        print(f"Mark result: {result}")
        return result
    else:
        print("No unread messages to mark")
        return {"success": False, "error": "No messages to mark"}

async def test_reply():
    """Test sending a reply to an email"""
    print("\nTesting reply to email...")
    
    # Get one message to reply to
    check_result = await check_emails(
        config=TEST_CONFIG,
        folder="INBOX",
        criteria={
            "since_date": datetime.now() - timedelta(days=180)
        },
        batch_size=1  # Just get one message
    )
    
    if check_result["success"] and check_result["messages"]:
        original_message = check_result["messages"][0]
        
        result = await send_email(
            config=TEST_CONFIG,
            to=original_message["from"],
            subject=original_message["subject"],
            body="This is a test reply.",
            reply_to_message=original_message,
            headers={"X-Test-Reply": "true"}
        )
        
        print(f"Reply result: {result}")
        return result
    else:
        print("No messages to reply to")
        return {"success": False, "error": "No messages to reply to"}

async def run_tests():
    """Run all tests"""
    try:
        # Initialize the provider
        await init_provider(TEST_CONFIG)
        
        # Run tests
        #await test_send_email()
        await test_check_emails_with_pagination()
        #await test_mark_processed()
        #await test_reply()
        
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error during tests: {str(e)}\n{trace}")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())
