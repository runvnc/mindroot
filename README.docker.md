# Running MindRoot with Docker

This guide explains how to run MindRoot using Docker and Docker Compose.

The Docker configuration uses Python 3.12.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Quick Start

1. Clone or download the MindRoot repository
2. Navigate to the MindRoot directory
3. Configure environment variables in `docker-compose.yml`
4. Build and start the containers:

```bash
docker-compose up -d
```

5. Access MindRoot at http://localhost:8010

## Configuration

Edit the `docker-compose.yml` file to configure your environment variables:

```yaml
environment:
  - JWT_SECRET_KEY=your_jwt_secret_key  # Required: change this to a secure random string
  - OPENAI_API_KEY=your_openai_api_key  # Optional: for OpenAI integration
  - ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional: for Anthropic integration
  - REQUIRE_EMAIL_VERIFY=false  # Optional: set to true to require email verification
  # SMTP settings (required if REQUIRE_EMAIL_VERIFY=true)
  - SMTP_HOST=your_smtp_host
  - SMTP_PORT=your_smtp_port
  - SMTP_USER=your_smtp_username
  - SMTP_PASSWORD=your_smtp_password
  - SMTP_FROM=your_from_email
```

## Persistent Data

The Docker setup mounts these directories as volumes to persist data outside the container:

- `./data`: Chat history, sessions, and other data
- `./models`: AI models
- `./personas`: Agent personas
- `./imgs`: Images

## Building the Docker Image

If you've made changes to the Dockerfile or want to rebuild the image:

```bash
docker-compose build
```

## Stopping the Container

```bash
docker-compose down
```

## Viewing Logs

```bash
docker-compose logs -f
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with the mounted volumes, you may need to adjust the permissions of the directories:

```bash
chmod -R 777 data models personas imgs
```

### Container Won't Start

Check the logs for error messages:

```bash
docker-compose logs
### Missing libgl or OpenCV Dependencies

The Dockerfile includes `libgl1-mesa-dev` which is required for some image processing functionality. If you encounter errors related to OpenCV or other image processing libraries, you may need to install additional dependencies in the Dockerfile:

```bash
```

### Can't Connect to MindRoot

Ensure the container is running:

```bash
docker-compose ps
```

Check if the port mapping is correct in the `docker-compose.yml` file.
