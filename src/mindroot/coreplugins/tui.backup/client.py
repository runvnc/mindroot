"""MindRoot API Client for TUI."""
import httpx
import json
import os
from typing import Optional, Dict, List, AsyncIterator
from urllib.parse import urljoin

class MindRootClient:
    """Async client for MindRoot API."""

    def __init__(self, base_url: str=None, api_key: str=None, debug: bool=False):
        self.base_url = base_url or os.getenv('MINDROOT_BASE_URL', 'http://localhost:8010')
        self.api_key = api_key or os.getenv('MINDROOT_API_KEY')
        self.debug = debug or os.getenv('MR_DEBUG', 'false').lower() == 'true'
        if not self.api_key:
            raise ValueError('MINDROOT_API_KEY must be set in environment or .env file')
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(300.0, connect=10.0), follow_redirects=True)

    async def create_session(self, agent_name: str, client_cwd: str=None) -> str:
        """Create a new chat session and return the log_id."""
        try:
            sys_msg = '\nYou are running via the terminal (TUI) interface. When the user refers to files or direcotires,\nthey are referring to their working dir, not the server process working dir.\n\nSo they may refer to a relative file path but you would need to use the absolute path relative\nto their TUI startup working dir.'
            response = await self.client.get(f'/agent/{agent_name}', params={'api_key': self.api_key, 'tui': 'true', 'client_cwd': client_cwd or os.getcwd(), 'context': sys_msg}, follow_redirects=True)
            final_url = str(response.url)
            log_id = final_url.split('/')[-1]
            if '?' in log_id:
                log_id = log_id.split('?')[0]
            return log_id
        except Exception as e:
            raise

    async def send_message(self, log_id: str, message: str) -> Dict:
        """Send a message to the agent."""
        try:
            message_parts = [{'type': 'text', 'text': message}]
            response = await self.client.post(f'/chat/{log_id}/send', json=message_parts, headers={'Authorization': f'Bearer {self.api_key}'})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise

    async def stream_events(self, log_id: str) -> AsyncIterator[Dict]:
        """Stream SSE events from the agent."""
        try:
            async with self.client.stream('GET', f'/chat/{log_id}/events', headers={'Authorization': f'Bearer {self.api_key}'}) as response:
                event_type = None
                async for line in response.aiter_lines():
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                    elif line.startswith('data:'):
                        try:
                            data = json.loads(line[5:].strip())
                            if event_type:
                                yield {'event': event_type, 'data': data}
                                event_type = None
                        except json.JSONDecodeError as e:
                            continue
        except Exception as e:
            raise

    async def get_history(self, agent_name: str, log_id: str) -> List[Dict]:
        """Get chat history for a session."""
        try:
            response = await self.client.get(f'/history/{agent_name}/{log_id}', headers={'Authorization': f'Bearer {self.api_key}'})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise

    async def run_task(self, agent_name: str, instructions: str, client_cwd: str=None) -> Dict:
        """Run a task and get the result (non-interactive mode)."""
        try:
            params = {'api_key': self.api_key}
            if client_cwd:
                params['tui'] = 'true'
                params['client_cwd'] = client_cwd
            response = await self.client.post(f'/task/{agent_name}', json={'instructions': instructions}, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise
        except Exception as e:
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()