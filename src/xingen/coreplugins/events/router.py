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
            async for line in response.content:
                if line:
                    try:
                        msg = line.decode()
                        if msg.startswith('data:'):
                            # Parse the SSE data and add conversation ID
                            data = json.loads(msg[5:])  # Skip 'data:' prefix
                            data['conversation_id'] = conv_id
                            # Reconstruct SSE message
                            msg = f"data: {json.dumps(data)}"
                    except Exception as e:
                        print(f"Error processing SSE message: {e}")
                    await queue.put(msg)

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

    #print blue back with yellow text bold
    print(f"\033[1;30;46;33mMultiplexed events for conversations: {conversation_ids} access token= {access_token}\033[0m")
        
    # Create queue for aggregated messages
    main_queue = asyncio.Queue()

    # Get base URL for chat events
    base_url = str(request.base_url).rstrip('/')
    
    tasks = []
    for conv_id in conversation_ids:
        # Construct URL for each conversation's events
        url = f"{base_url}/chat/{conv_id}/events"
        task = asyncio.create_task(
            create_sse_client(url, access_token, main_queue, conv_id)
        )
        # print with blue background and yellow text, all bold
        print(f"\033[1;30;46;33mCreated SSE client for conversation {conv_id} {url}\033[0m")
        tasks.append(task)

    async def event_generator():
        try:
            while True:
                message = await main_queue.get()
                # print with blue background and yellow text, all bold
                print(f"\033[1;30;46;33mReceived message: {message}\033[0m")
                if message:
                    yield message
        except asyncio.CancelledError:
            # Cancel all SSE client tasks
            for task in tasks:
                task.cancel()
            raise

    return EventSourceResponse(event_generator())

