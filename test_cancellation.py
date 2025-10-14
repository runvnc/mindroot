#!/usr/bin/env python3
"""
Test script to verify the send_message_to_agent cancellation functionality
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, '/files/mindroot/src')

from mindroot.coreplugins.chat.services import (
    send_message_to_agent, 
    active_send_tasks,
    cancel_active_send_task,
    get_active_send_tasks
)
from mindroot.lib.chatcontext import ChatContext
from mindroot.lib.providers.services import service_manager
from mindroot.lib.providers.commands import command_manager

async def test_cancellation():
    """
    Test the cancellation functionality
    """
    print("Testing send_message_to_agent cancellation functionality...")
    
    # Test parameters
    test_log_id = "test_cancellation_session"
    test_message = "This is a test message for cancellation testing"
    
    # Create a mock context (this would normally be created by the system)
    try:
        context = ChatContext(command_manager, service_manager, "test_user")
        context.log_id = test_log_id
        context.agent_name = "test_agent"
        context.current_model = "gpt-3.5-turbo"  # Use a simple model for testing
        
        print(f"Created test context for log_id: {test_log_id}")
        
        # Test 1: Check initial state
        print("\n=== Test 1: Initial State ===")
        active_tasks = await get_active_send_tasks()
        print(f"Active tasks before test: {active_tasks}")
        
        # Test 2: Start a task and check it's registered
        print("\n=== Test 2: Starting Task ===")
        
        # Create a task that will run for a while
        async def long_running_task():
            try:
                # This should trigger the cancellation detection
                result = await send_message_to_agent(
                    session_id=test_log_id,
                    message=test_message,
                    max_iterations=50,  # High number to ensure it runs long enough
                    context=context,
                    user={"user": "test_user"}
                )
                print(f"Task completed with result: {result}")
                return result
            except asyncio.CancelledError:
                print("Task was successfully cancelled!")
                raise
        
        task = asyncio.create_task(long_running_task())
        
        # Give it a moment to start and register
        await asyncio.sleep(0.5)
        
        # Check if task is registered
        active_tasks = await get_active_send_tasks()
        print(f"Active tasks after starting: {active_tasks}")
        
        if test_log_id in active_tasks['active_tasks']:
            print("✓ Task successfully registered in active_send_tasks")
        else:
            print("✗ Task not found in active_send_tasks")
            return False
        
        # Test 3: Cancel the task
        print("\n=== Test 3: Cancelling Task ===")
        
        cancel_result = await cancel_active_send_task(test_log_id, context=context)
        print(f"Cancel result: {cancel_result}")
        
        # Wait for cancellation to complete
        try:
            await asyncio.wait_for(task, timeout=3.0)
        except asyncio.CancelledError:
            print("✓ Task was cancelled as expected")
        except asyncio.TimeoutError:
            print("✗ Task did not cancel within timeout")
            task.cancel()
            return False
        
        # Test 4: Check cleanup
        print("\n=== Test 4: Checking Cleanup ===")
        
        await asyncio.sleep(0.5)  # Give cleanup time
        
        active_tasks = await get_active_send_tasks()
        print(f"Active tasks after cancellation: {active_tasks}")
        
        if test_log_id not in active_tasks['active_tasks']:
            print("✓ Task successfully cleaned up from active_send_tasks")
        else:
            print("✗ Task still found in active_send_tasks after cancellation")
            return False
        
        # Test 5: Test starting a new task after cancellation
        print("\n=== Test 5: Starting New Task After Cancellation ===")
        
        # This should work without issues
        try:
            # Start a short task
            short_task = asyncio.create_task(
                send_message_to_agent(
                    session_id=test_log_id,
                    message="Short test message",
                    max_iterations=1,  # Just one iteration
                    context=context,
                    user={"user": "test_user"}
                )
            )
            
            # Wait for it to complete
            await asyncio.wait_for(short_task, timeout=5.0)
            print("✓ New task started successfully after cancellation")
            
        except Exception as e:
            print(f"✗ Error starting new task after cancellation: {e}")
            return False
        
        print("\n=== All Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting cancellation test...")
    
    try:
        result = asyncio.run(test_cancellation())
        if result:
            print("\n🎉 All tests passed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
