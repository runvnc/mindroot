# MindRoot Registry

A comprehensive registry system for MindRoot plugins and agents, featuring semantic search, user authentication, and seamless integration with the MindRoot admin interface.

## Features

- 🔍 **Semantic Search**: ChromaDB-powered vector search for intelligent plugin/agent discovery
- 🔐 **Authentication**: JWT-based user authentication with registration
- 📦 **Publishing**: Easy publishing of plugins and agents to the registry
- 📊 **Analytics**: Download tracking, ratings, and usage statistics
- 🌐 **Web Interface**: Clean web interface and comprehensive API
- 🔗 **Integration**: Seamless integration with MindRoot admin interface

## Quick Start

### 1. Install Dependencies

```bash
cd /files/mindroot/registry_website
pip install -r requirements.txt
```

### 2. Start the Registry

```bash
python start_registry.py
```

This will:
- Initialize the database
- Create an admin user (username: `admin`, password: `admin123`)
- Initialize the vector store
- Start the server on http://localhost:8000

### 3. Access the Registry

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MindRoot Admin**: Navigate to the Registry tab in your MindRoot admin interface

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /token` - Login and get access token

### Content Management
- `POST /publish` - Publish a plugin or agent
- `GET /search` - Search for content with semantic search
- `GET /content/{id}` - Get specific content details
- `POST /install/{id}` - Track an installation
- `POST /rate` - Rate content

### Statistics
- `GET /stats` - Get registry statistics
- `POST /admin/rebuild-index` - Rebuild vector search index (admin only)

## Usage Examples

### Register a User

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "email": "dev@example.com",
    "password": "securepassword"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=developer&password=securepassword"
```

### Search for Plugins

```bash
curl "http://localhost:8000/search?query=web%20search&category=plugin&semantic=true"
```

### Publish a Plugin

```bash
curl -X POST "http://localhost:8000/publish" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Awesome Plugin",
    "description": "A plugin that does amazing things",
    "category": "plugin",
    "content_type": "mindroot_plugin",
    "version": "1.0.0",
    "github_url": "https://github.com/user/my-plugin",
    "commands": ["my_command"],
    "services": ["my_service"],
    "tags": ["utility", "automation"],
    "data": {
      "installation_notes": "Easy to install and configure"
    }
  }'
```

## Integration with MindRoot Admin

The registry integrates seamlessly with the MindRoot admin interface:

1. **Registry Tab**: Access the registry directly from the admin interface
2. **Login**: Authenticate with your registry account
3. **Search**: Find plugins and agents using semantic search
4. **Install**: One-click installation of registry content
5. **Publish**: Publish your local plugins and agents to the registry

### Using the Registry Tab

1. Open your MindRoot admin interface (`/admin`)
2. Click on the "Registry" tab
3. Login with your registry credentials
4. Search for plugins or agents
5. Click "Install" to add them to your MindRoot instance
6. Use the "Publish" tab to share your own content

## Database Schema

The registry uses SQLite with the following main tables:

- **users**: User accounts and authentication
- **contents**: Plugins and agents with metadata
- **ratings**: User ratings and reviews
- **install_logs**: Installation tracking for analytics

## Vector Search

The registry uses ChromaDB for semantic search capabilities:

- **Automatic Indexing**: Content is automatically indexed when published
- **Semantic Similarity**: Find related content even with different keywords
- **Metadata Filtering**: Filter by category, tags, commands, etc.
- **Relevance Scoring**: Results ranked by semantic similarity

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: JWT secret key (change in production!)
- `REGISTRY_HOST`: Server host (default: 0.0.0.0)
- `REGISTRY_PORT`: Server port (default: 8000)

### Production Setup

1. **Change Secret Key**: Update `SECRET_KEY` in `authentication.py`
2. **Database**: Consider PostgreSQL for production
3. **CORS**: Configure CORS settings for your domain
4. **HTTPS**: Use a reverse proxy like nginx for HTTPS
5. **Monitoring**: Add logging and monitoring

## Development

### Project Structure

```
registry_website/
├── main.py              # FastAPI application
├── database.py          # Database models
├── authentication.py   # JWT authentication
├── vector_store.py      # ChromaDB integration
├── start_registry.py    # Startup script
├── requirements.txt     # Dependencies
├── templates/           # HTML templates
│   └── index.html
└── README.md           # This file
```

### Adding New Features

1. **API Endpoints**: Add new routes in `main.py`
2. **Database Models**: Extend models in `database.py`
3. **Search Features**: Enhance `vector_store.py`
4. **Frontend**: Update templates or admin components

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Change the port in `start_registry.py`
2. **Database Errors**: Delete `mindroot_registry.db` and restart
3. **ChromaDB Issues**: Delete `registry_chroma_db/` directory and restart
4. **Authentication Errors**: Check JWT secret key configuration

### Logs

The server logs will show:
- API requests and responses
- Database operations
- Vector store operations
- Authentication events

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the MindRoot ecosystem. See the main MindRoot repository for license information.

## Support

For support and questions:
- Check the MindRoot documentation
- Open an issue in the MindRoot repository
- Join the MindRoot community discussions
