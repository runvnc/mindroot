from fastapi import APIRouter, Depends, HTTPException, Form, Response, Request, Query
from lib.route_decorators import public_routes, public_route
from sse_starlette.sse import EventSourceResponse
from typing import List
import asyncio
import aiohttp
import json

router = APIRouter()

async def create_sse_client(url: str, access_token: str, queue: asyncio.Queue, conv_id: str):
    """Creates internal SSE client that forwards to queue with conversation ID"""
    headers = {
        'Cookie': f'access_token={access_token}'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            current_event = None
            current_data = None
            
            async for line in response.content:
                if line:
                    try:
                        decoded_line = line.decode().strip()
                        
                        # Handle event line
                        if decoded_line.startswith('event:'):
                            current_event = decoded_line.split(':', 1)[1].strip()
                            continue
                            
                        # Handle data line
                        if decoded_line.startswith('data:'):
                            current_data = decoded_line.split(':', 1)[1].strip()
                            try:
                                # Parse and add conversation ID
                                data = json.loads(current_data)
                                data['conversation_id'] = conv_id
                                current_data = json.dumps(data)
                            except Exception as e:
                                print(f"Error processing data JSON: {e}")
                            
                            # Reconstruct SSE message
                            if current_event:
                                await queue.put(f"event: {current_event}\ndata: {current_data}\n\n")
                            else:
                                await queue.put(f"data: {current_data}\n\n")
                            
                            current_event = None
                            current_data = None
                            
                    except Exception as e:
                        print(f"Error processing SSE line: {e}")

@router.get("/events/multi")
async def multiplexed_events(
    request: Request,
    conversation_ids: List[str] = Query(None)
):
    if not conversation_ids:
        raise HTTPException(status_code=400, detail="conversation_ids parameter is required")

    # Get access token from cookie
    access_token = request.cookies.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")

    # Create queue for aggregated messages
    main_queue = asyncio.Queue()

    # Get base URL for chat events
    base_url = str(request.base_url).rstrip('/')
    
    tasks = []
    for conv_id in conversation_ids:
        url = f"{base_url}/chat/{conv_id}/events"
        task = asyncio.create_task(
            create_sse_client(url, access_token, main_queue, conv_id)
        )
        tasks.append(task)

    async def event_generator():
        try:
            while True:
                message = await main_queue.get()
                if message:
                    yield message
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            raise

    return EventSourceResponse(event_generator())

