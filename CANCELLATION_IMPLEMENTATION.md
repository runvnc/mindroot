# send_message_to_agent Cancellation Implementation

## Overview

This implementation adds robust detection and cancellation capabilities for in-progress `send_message_to_agent` calls in the MindRoot chat system. It prevents multiple simultaneous processing for the same chat session and provides immediate cancellation of in-progress tasks.

## Features

### 1. Automatic Detection and Cancellation
- **Prevention**: Automatically detects and cancels existing `send_message_to_agent` tasks for a session before starting new ones
- **Immediate Cancellation**: Provides instant cancellation of in-progress tasks
- **Clean Integration**: Works seamlessly with existing architecture

### 2. Enhanced Error Handling
- **Graceful Cancellation**: Proper handling of `asyncio.CancelledError` throughout the processing loop
- **Resource Cleanup**: Automatic cleanup of SSE connections and other resources
- **Memory Management**: Prevents memory leaks through proper task cleanup

### 3. Monitoring and Debugging
- **Active Task Tracking**: Global tracking of all active tasks by session ID
- **Debug Endpoints**: HTTP endpoints for monitoring and debugging active tasks
- **Comprehensive Logging**: Detailed logging for troubleshooting

## Implementation Details

### Core Components

#### 1. Global State Management
```python
# In services.py
active_send_tasks = {}  # Tracks active tasks by log_id
```

Each entry contains:
- `task`: The asyncio.Task reference
- `created_at`: Timestamp when task was created
- `context`: The chat context for the task

#### 2. Enhanced send_message_to_agent Function
The function now includes:
- **Pre-execution check**: Cancels existing tasks for the same session
- **Task registration**: Registers current task in global dictionary
- **Cancellation checkpoints**: Multiple points throughout the processing loop
- **Cleanup handlers**: Proper cleanup on completion and cancellation

#### 3. New Service Functions

##### cancel_active_send_task(log_id, context=None)
Cancels an active task for a specific session.
```python
result = await cancel_active_send_task("session_123", context=context)
# Returns: {"status": "cancelled", "log_id": "session_123"}
```

##### get_active_send_tasks(context=None)
Gets information about all active tasks.
```python
result = await get_active_send_tasks()
# Returns: {"status": "ok", "active_tasks": {"session_123": {...}}}
```

##### cleanup_completed_tasks(context=None)
Cleans up completed tasks to prevent memory leaks.
```python
result = await cleanup_completed_tasks()
# Returns: {"status": "ok", "cleaned_up": ["session_123"]}
```

### HTTP API Endpoints

#### 1. Enhanced Cancellation Endpoint
```
POST /chat/{log_id}/{task_id}/cancel
```
Now actually cancels the asyncio task instead of just setting flags.

#### 2. Direct Task Cancellation
```
POST /chat/{log_id}/cancel_send_task
```
Cancels the active `send_message_to_agent` task for a session.

#### 3. Active Tasks Monitoring
```
GET /chat/{log_id}/active_tasks
```
Gets information about active tasks for a specific session.

#### 4. Global Active Tasks
```
GET /chat/active_send_tasks
```
Gets information about all active tasks across all sessions.

#### 5. Cleanup Endpoint
```
POST /chat/cleanup_completed_tasks
```
Manually triggers cleanup of completed tasks.

## Usage Examples

### 1. Automatic Cancellation (Default Behavior)
```python
# When a new message is sent, any existing task for the same session
# is automatically cancelled before the new one starts
result = await send_message_to_agent(
    session_id="user_session_123",
    message="Hello, how are you?",
    context=context,
    user=user
)
```

### 2. Manual Cancellation
```python
# Cancel an active task manually
from mindroot.coreplugins.chat.services import cancel_active_send_task

result = await cancel_active_send_task("user_session_123", context=context)
if result["status"] == "cancelled":
    print("Task cancelled successfully")
```

### 3. Monitoring Active Tasks
```python
# Check what tasks are currently active
from mindroot.coreplugins.chat.services import get_active_send_tasks

result = await get_active_send_tasks()
for log_id, task_info in result["active_tasks"].items():
    print(f"Session {log_id}: active={task_info['active']}")
```

### 4. HTTP API Usage

#### Cancel a task via HTTP:
```bash
curl -X POST "http://localhost:8000/chat/user_session_123/cancel_send_task" \
  -H "Authorization: Bearer your_token"
```

#### Check active tasks via HTTP:
```bash
curl -X GET "http://localhost:8000/chat/active_send_tasks" \
  -H "Authorization: Bearer your_token"
```

## Integration with Existing Systems

### 1. Context Integration
The implementation integrates with existing context flags:
- `context.data['task_cancelled']`: Set when task is cancelled
- `context.data['cancel_current_turn']`: Existing flag for turn cancellation

### 2. SSE Connection Cleanup
When a task is cancelled, all associated SSE connections are properly closed:
```python
# Automatic cleanup of SSE connections
if session_id in sse_clients:
    for queue in sse_clients[session_id]:
        await queue.put({'event': 'close', 'data': 'Task cancelled'})
```

### 3. Pipeline Integration
The cancellation works with the existing pipeline system and doesn't interfere with other processing stages.

## Testing

A comprehensive test script is provided at `/files/mindroot/test_cancellation.py`.

### Running the Test:
```bash
cd /files/mindroot
python test_cancellation.py
```

The test covers:
1. Task registration and tracking
2. Cancellation functionality
3. Cleanup after cancellation
4. Starting new tasks after cancellation

## Performance Considerations

### 1. Memory Usage
- The global `active_send_tasks` dictionary is automatically cleaned up
- Completed tasks are removed to prevent memory leaks
- A cleanup service is provided for manual cleanup

### 2. Cancellation Overhead
- Cancellation checks are lightweight and don't impact normal processing
- Task cancellation is immediate and doesn't wait for current operations
- Cleanup operations are asynchronous and non-blocking

### 3. Scalability
- The system scales with the number of concurrent sessions
- Each session maintains only one active task at a time
- Global tracking is O(1) for lookups and updates

## Error Handling

### 1. Cancellation Errors
- `asyncio.CancelledError` is handled gracefully throughout the processing loop
- Resources are properly cleaned up even if cancellation occurs mid-operation
- Error logging provides detailed information for debugging

### 2. Race Conditions
- The implementation handles race conditions between task creation and cancellation
- Atomic operations ensure consistent state
- Timeout handling prevents hanging cancellations

### 3. Context Errors
- Missing or invalid contexts are handled gracefully
- Fallback mechanisms ensure system stability
- Error recovery is built into all operations

## Backward Compatibility

The implementation maintains full backward compatibility:
- Existing code continues to work without changes
- All existing APIs remain functional
- New features are additive and don't break existing functionality

## Future Enhancements

Potential future improvements:
1. **Task Prioritization**: Add priority levels for different types of tasks
2. **Cancellation Policies**: Configurable cancellation behavior per agent or user
3. **Metrics and Monitoring**: Integration with monitoring systems
4. **Batch Operations**: Bulk cancellation and cleanup operations
5. **Persistence**: Optional persistence of task state across restarts

## Troubleshooting

### Common Issues

#### 1. Task Not Cancelling
- Check if the task is properly registered in `active_send_tasks`
- Verify the task hasn't already completed
- Check for proper context handling

#### 2. Memory Leaks
- Ensure `cleanup_completed_tasks()` is called periodically
- Monitor the size of `active_send_tasks` dictionary
- Check for exceptions in cleanup handlers

#### 3. SSE Connection Issues
- Verify SSE connections are properly closed on cancellation
- Check for network issues preventing cleanup
- Monitor client-side connection handling

### Debug Information

Enable debug logging by setting environment variable:
```bash
export MR_DEBUG=True
```

This will provide detailed logging of:
- Task registration and cancellation
- Cleanup operations
- Error conditions
- State transitions

## Conclusion

This implementation provides a robust, scalable solution for managing and cancelling `send_message_to_agent` tasks in the MindRoot chat system. It ensures system stability, prevents resource conflicts, and provides comprehensive monitoring and debugging capabilities.

The solution is production-ready and has been thoroughly tested for various scenarios including edge cases and error conditions.
