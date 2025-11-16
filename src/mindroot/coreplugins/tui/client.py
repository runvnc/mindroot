"""MindRoot API Client for TUI."""

import httpx
import json
import os
from typing import Optional, Dict, List, AsyncIterator
from urllib.parse import urljoin


class MindRootClient:
    """Async client for MindRoot API."""
    
    def __init__(self, base_url: str = None, api_key: str = None, debug: bool = False):
        self.base_url = base_url or os.getenv('MINDROOT_BASE_URL', 'http://localhost:8010')
        self.api_key = api_key or os.getenv('MINDROOT_API_KEY')
        self.debug = debug or os.getenv('MR_DEBUG', 'false').lower() == 'true'
        
        if not self.api_key:
            raise ValueError("MINDROOT_API_KEY must be set in environment or .env file")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(300.0, connect=10.0),
            follow_redirects=True
        )
        
        if self.debug:
            print(f"[DEBUG] MindRoot client initialized")
            print(f"[DEBUG] Base URL: {self.base_url}")
            print(f"[DEBUG] API Key: {self.api_key[:10]}...")
    
    async def create_session(self, agent_name: str) -> str:
        """Create a new chat session and return the log_id."""
        try:
            if self.debug:
                print(f"[DEBUG] Creating session for agent: {agent_name}")
            
            response = await self.client.get(
                f"/agent/{agent_name}",
                params={"api_key": self.api_key}
            )
            
            if self.debug:
                print(f"[DEBUG] Session creation response status: {response.status_code}")
                print(f"[DEBUG] Final URL: {response.url}")
            
            # The endpoint redirects to /session/{agent_name}/{log_id}
            # Extract log_id from the final URL
            final_url = str(response.url)
            log_id = final_url.split('/')[-1]
            
            # Remove any query parameters
            if '?' in log_id:
                log_id = log_id.split('?')[0]
            
            if self.debug:
                print(f"[DEBUG] Extracted log_id: {log_id}")
            
            return log_id
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error creating session: {e}")
            raise
    
    async def send_message(self, log_id: str, message: str) -> Dict:
        """Send a message to the agent."""
        try:
            if self.debug:
                print(f"[DEBUG] Sending message to log_id: {log_id}")
                print(f"[DEBUG] Message: {message[:100]}...")
            
            message_parts = [{"type": "text", "text": message}]
            
            response = await self.client.post(
                f"/chat/{log_id}/send",
                json=message_parts,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if self.debug:
                print(f"[DEBUG] Send message response status: {response.status_code}")
                print(f"[DEBUG] Response: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error sending message: {e}")
            raise
    
    async def stream_events(self, log_id: str) -> AsyncIterator[Dict]:
        """Stream SSE events from the agent."""
        try:
            if self.debug:
                print(f"[DEBUG] Starting event stream for log_id: {log_id}")
            
            async with self.client.stream(
                "GET",
                f"/chat/{log_id}/events",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if self.debug:
                    print(f"[DEBUG] Event stream response status: {response.status_code}")
                
                event_type = None
                async for line in response.aiter_lines():
                    if self.debug and line:
                        print(f"[DEBUG] SSE line: {line}")
                    
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                    elif line.startswith('data:'):
                        try:
                            data = json.loads(line[5:].strip())
                            if event_type:
                                yield {"event": event_type, "data": data}
                                event_type = None
                        except json.JSONDecodeError as e:
                            if self.debug:
                                print(f"[DEBUG] JSON decode error: {e}")
                            continue
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error in event stream: {e}")
            raise
    
    async def get_history(self, agent_name: str, log_id: str) -> List[Dict]:
        """Get chat history for a session."""
        try:
            if self.debug:
                print(f"[DEBUG] Getting history for {agent_name}/{log_id}")
            
            response = await self.client.get(
                f"/history/{agent_name}/{log_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if self.debug:
                print(f"[DEBUG] History response status: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error getting history: {e}")
            raise
    
    async def run_task(self, agent_name: str, instructions: str) -> Dict:
        """Run a task and get the result (non-interactive mode)."""
        try:
            if self.debug:
                print(f"[DEBUG] Running task with agent: {agent_name}")
                print(f"[DEBUG] Instructions: {instructions[:100]}...")
            
            response = await self.client.post(
                f"/task/{agent_name}",
                json={"instructions": instructions},
                params={"api_key": self.api_key}
            )
            
            if self.debug:
                print(f"[DEBUG] Task response status: {response.status_code}")
                print(f"[DEBUG] Response: {response.text[:500]}...")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if self.debug:
                print(f"[DEBUG] HTTP error: {e}")
                print(f"[DEBUG] Response text: {e.response.text}")
            raise
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error running task: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
