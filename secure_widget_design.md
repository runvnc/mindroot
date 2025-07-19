# Secure Widget Embedding System Design

## Current Security Issue
The existing api-key-script.js exposes API keys directly in the generated JavaScript code, making them visible to anyone who views the page source.

## Proposed Secure Solution

### 1. Widget Token System
- Generate unique widget tokens (e.g., `abcd1234`)
- Store widget configurations in `data/widgets/{token}.json`
- Configuration includes: API key, agent name, base URL, optional styling

### 2. Secure Embed Endpoint
New endpoint: `/chat/embed/{token}`
- Validates widget token
- Reads configuration from `data/widgets/{token}.json`
- Uses stored API key for internal authentication
- Returns JavaScript that creates secure iframe
- API key never exposed to frontend

### 3. Simple Embed Code
Users get clean embed code:
```html
<script src="http://localhost:8012/chat/embed/abcd1234"></script>
```

### 4. Widget Configuration File Structure
```json
{
  "token": "abcd1234",
  "api_key": "actual_api_key_here",
  "agent_name": "my_agent",
  "base_url": "http://localhost:8012",
  "created_at": "2025-01-01T00:00:00Z",
  "created_by": "admin",
  "description": "Widget for company website",
  "styling": {
    "position": "bottom-right",
    "theme": "dark"
  }
}
```

### 5. Implementation Components

#### A. Widget Management Service
- Create/delete widget tokens
- Store/retrieve widget configurations
- Validate widget tokens

#### B. Secure Embed Route
- `/chat/embed/{token}` - Returns JavaScript for embedding
- `/chat/widget/{token}/session` - Creates secure chat session

#### C. Updated Admin Interface
- Replace API key exposure with widget token generation
- Manage widget tokens (create, list, delete)
- Show simple embed code instead of complex script

#### D. Security Benefits
- API keys never exposed to frontend
- Widget tokens can be revoked without changing API keys
- Centralized widget management
- Audit trail of widget usage

### 6. Implementation Flow
1. Admin creates widget token with agent/API key configuration
2. Widget config stored securely in `data/widgets/{token}.json`
3. Admin copies simple embed script: `<script src="/chat/embed/{token}"></script>`
4. When script loads:
   - Server validates token
   - Creates secure session using stored API key
   - Returns JavaScript that creates iframe with session URL
   - No API key ever sent to browser

### 7. Backward Compatibility
- Keep existing `/agent/{agent_name}?api_key=...` for direct API usage
- New widget system is additive, doesn't break existing functionality
