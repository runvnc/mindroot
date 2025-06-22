# MindRoot Registry Implementation Plan

## Overview
Implement a comprehensive registry system for MindRoot plugins and agents, similar to npm registry but tailored for MindRoot ecosystem. The system will integrate with the existing admin interface and provide semantic search capabilities using ChromaDB.

## Current State Analysis

### Existing Components
1. **Registry Website**: Basic FastAPI backend with JWT authentication in `/files/mindroot/registry_website`
2. **Admin Interface**: Web component-based admin with plugin/agent management
3. **Plugin System**: Supports GitHub, local, and PyPI installation sources
4. **Agent System**: Can import from GitHub and local sources
5. **Index System**: Existing index structure for plugins/agents
6. **ChromaDB**: Available via mr_kb plugin for vector search

### Current Capabilities
- Plugin installation from multiple sources
- Agent creation and management
- Basic authentication system
- Web component architecture

## Implementation Plan

### Phase 1: Enhanced Registry Backend

#### 1.1 Database Schema Updates
Extend the existing Content model to support MindRoot-specific data:

```python
class Content(Base):
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    category = Column(String, index=True)  # 'plugin' or 'agent'
    content_type = Column(String)  # 'mindroot_plugin', 'mindroot_agent'
    data = Column(JSON)  # Plugin/agent specific data
    version = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # New MindRoot-specific fields
    github_url = Column(String)
    pypi_module = Column(String)
    commands = Column(JSON)  # List of commands
    services = Column(JSON)  # List of services
    tags = Column(JSON)  # List of tags for categorization
    download_count = Column(Integer, default=0)
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

#### 1.2 ChromaDB Integration
Add vector search capabilities:

```python
import chromadb
from chromadb.config import Settings

class RegistryVectorStore:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory="./registry_chroma_db"
        ))
        self.collection = self.client.get_or_create_collection(
            name="mindroot_registry",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_item(self, item_id: str, description: str, metadata: dict):
        self.collection.add(
            documents=[description],
            metadatas=[metadata],
            ids=[item_id]
        )
    
    def search(self, query: str, n_results: int = 10, filter_dict: dict = None):
        return self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict
        )
```

#### 1.3 Enhanced API Endpoints

```python
# New endpoints for registry functionality
@app.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # User registration endpoint
    pass

@app.post("/publish")
def publish_content(content: ContentCreate, db: Session = Depends(get_db)):
    # Enhanced publish with vector indexing
    pass

@app.get("/search")
def search_content(query: str, category: str = None, limit: int = 20):
    # Semantic search with ChromaDB
    pass

@app.post("/install/{content_id}")
def track_install(content_id: int, db: Session = Depends(get_db)):
    # Track installation statistics
    pass
```

### Phase 2: Registry Admin Component

#### 2.1 Registry Manager Component
Create `/files/mindroot/src/mindroot/coreplugins/admin/static/js/registry-manager.js`:

```javascript
import { BaseEl } from '/admin/static/js/base.js';
import { html, css } from '/admin/static/js/lit-core.min.js';

class RegistryManager extends BaseEl {
  static properties = {
    isLoggedIn: { type: Boolean },
    searchResults: { type: Array },
    registryUrl: { type: String },
    currentUser: { type: Object }
  };

  constructor() {
    super();
    this.isLoggedIn = false;
    this.searchResults = [];
    this.registryUrl = 'http://localhost:8000'; // Default registry URL
    this.currentUser = null;
  }

  async login(username, password) {
    // Login to registry
  }

  async search(query, category = null) {
    // Search registry with semantic search
  }

  async publish(itemData) {
    // Publish plugin/agent to registry
  }

  _render() {
    return html`
      <div class="registry-manager">
        ${this.isLoggedIn ? this.renderLoggedIn() : this.renderLogin()}
      </div>
    `;
  }
}
```

#### 2.2 Integration with Admin Interface
Add Registry tab to admin template:

```jinja2
<!-- In admin.jinja2 -->
<details>
  <summary>
    <span class="material-icons">cloud</span>
    <span>Registry</span>
  </summary>
  <div class="details-content">
    <registry-manager theme="dark" scope="local"></registry-manager>
  </div>
</details>
```

### Phase 3: Enhanced Plugin/Agent Management

#### 3.1 Plugin Manager Enhancements
Add registry search to existing plugin-manager component:

```javascript
// Add to plugin-manager.js
async searchRegistry(query) {
  const response = await fetch(`${this.registryUrl}/search?query=${query}&category=plugin`);
  const results = await response.json();
  this.registryResults = results;
  this.requestUpdate();
}

async installFromRegistry(pluginId) {
  // Install plugin from registry
  const response = await fetch(`${this.registryUrl}/install/${pluginId}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${this.authToken}` }
  });
  // Handle installation
}
```

#### 3.2 Agent Editor Enhancements
Similar enhancements for agent-editor component.

### Phase 4: Registry Website Updates

#### 4.1 Minimal Web Interface
Update the registry website to be primarily API-focused:

```html
<!-- Simple landing page -->
<!DOCTYPE html>
<html>
<head>
    <title>MindRoot Registry</title>
</head>
<body>
    <h1>MindRoot Registry</h1>
    <p>Welcome to the MindRoot Plugin and Agent Registry</p>
    
    <h2>For Users</h2>
    <p>To search and install plugins/agents, use the Registry tab in your MindRoot admin interface at <code>/admin</code></p>
    
    <h2>For Developers</h2>
    <p>API Documentation: <a href="/docs">/docs</a></p>
    
    <h2>Browse</h2>
    <div id="browse-interface">
        <!-- Simple browse interface -->
    </div>
</body>
</html>
```

## Implementation Steps

### Step 1: Registry Backend Enhancement
1. Update database schema in `registry_website/database.py`
2. Add ChromaDB integration
3. Enhance API endpoints in `registry_website/main.py`
4. Add user registration endpoint
5. Add semantic search functionality

### Step 2: Create Registry Admin Component
1. Create `registry-manager.js` component
2. Add authentication UI
3. Add search interface
4. Add publish interface
5. Integrate with admin template

### Step 3: Enhance Existing Components
1. Add registry search to plugin-manager
2. Add registry search to agent-editor
3. Add "Publish to Registry" buttons
4. Integrate installation workflows

### Step 4: Testing and Documentation
1. Test all registry functionality
2. Update documentation
3. Create user guides
4. Test semantic search accuracy

## Technical Considerations

### Security
- JWT token authentication
- Rate limiting for API endpoints
- Input validation and sanitization
- Secure package verification

### Performance
- ChromaDB indexing optimization
- Caching for search results
- Pagination for large result sets
- CDN for package distribution

### Scalability
- Database indexing strategy
- Vector store optimization
- API response caching
- Load balancing considerations

## Data Flow

1. **Publishing**: Developer publishes plugin/agent → Registry API → Database + ChromaDB
2. **Searching**: User searches → Admin UI → Registry API → ChromaDB → Results
3. **Installing**: User installs → Admin UI → Registry API → GitHub/PyPI → Local installation

## Integration Points

1. **Existing Plugin System**: Leverage current installation mechanisms
2. **Agent System**: Use existing agent import functionality
3. **Index System**: Maintain compatibility with current index format
4. **Admin Interface**: Follow existing web component patterns

## Success Metrics

1. Number of published plugins/agents
2. Search accuracy and relevance
3. Installation success rate
4. User adoption rate
5. Community engagement

This plan provides a comprehensive approach to implementing the MindRoot registry while leveraging existing infrastructure and maintaining compatibility with current systems.