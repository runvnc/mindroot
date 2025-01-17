import asyncio
from typing import Dict
from services import init_provider, check_emails
import traceback
import os
from datetime import datetime, timedelta

# Test configuration
TEST_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True,
    "email": "runvnc@gmail.com",
    "password": os.environ.get("GMAIL_APP_PASSWORD"),
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "batch_size": 50,
    "max_messages": 1000
}

async def test_batch_processing():
    """Test processing recent messages in batches"""
    print("\nTesting batch email processing...")
    
    # Calculate date 2 weeks ago
    two_weeks_ago = datetime.now() - timedelta(days=14)
    print(f"Fetching messages since: {two_weeks_ago.strftime('%Y-%m-%d')}")
    
    next_id = None
    batch_count = 0
    total_messages = 0
    processed_ids = set()  # Track processed message IDs to detect duplicates
    
    while True:
        print(f"\nFetching batch {batch_count + 1}...")
        result = await check_emails(
            config=TEST_CONFIG,
            folder="INBOX",
            criteria={
                "since_date": two_weeks_ago
            },
            batch_size=50,
            start_id=next_id
        )
        
        if not result["success"]:
            print(f"Error: {result['error']}")
            break
            
        messages = result["messages"]
        pagination = result["pagination"]
        
        # Check for duplicate messages
        current_ids = set(msg["id"] for msg in messages)
        duplicates = current_ids.intersection(processed_ids)
        if duplicates:
            print(f"Warning: Found {len(duplicates)} duplicate messages in this batch!")
        processed_ids.update(current_ids)
        
        print(f"Fetched {len(messages)} messages")
        total_messages += len(messages)
        
        # Print summary of messages in this batch
        print("\nBatch Summary:")
        for msg in messages:
            print(f"ID: {msg['id']}")
            print(f"From: {msg['from'][:60]}")
            print(f"Subject: {msg['subject'][:60] if msg['subject'] else 'No subject'}")
            print(f"Date: {msg['date']}")
            print("-" * 60)
        
        if pagination:
            print(f"\nPagination info:")
            print(f"Total messages available: {pagination['total_messages']}")
            print(f"Current batch: {batch_count + 1}")
            print(f"Total processed so far: {total_messages}")
            print(f"Next ID: {pagination['next_id']}")
            print(f"Has more: {pagination['has_more']}")
            
            if not pagination['has_more']:
                print("\nNo more messages to process")
                break
                
            next_id = pagination['next_id']
            batch_count += 1
            
            # Stop if we've reached max messages
            if total_messages >= TEST_CONFIG['max_messages']:
                print(f"\nReached maximum message limit ({TEST_CONFIG['max_messages']})")
                break
        else:
            print("\nNo pagination info - ending processing")
            break
    
    print(f"\nProcessing complete:")
    print(f"Total batches processed: {batch_count}")
    print(f"Total messages processed: {total_messages}")
    print(f"Unique messages processed: {len(processed_ids)}")
    return result

async def run_test():
    """Run the batch processing test"""
    try:
        # Initialize the provider
        await init_provider(TEST_CONFIG)
        await test_batch_processing()
        
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error during test: {str(e)}\n{trace}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(run_test())
