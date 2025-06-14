FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libgl1-mesa-dev \
     python3-distutils \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files to template directory
COPY . /app-template/

# Create virtual environment and install MindRoot in template
WORKDIR /app-template
RUN python -m venv .venv
RUN .venv/bin/pip install --upgrade pip setuptools wheel
RUN .venv/bin/pip install .

# Create necessary directories
RUN mkdir -p /app/imgs \
    /app/data/chat \
    /app/models \
    /app/models/face \
    /app/models/llm \
    /app/static/personas \
    /app/personas \
    /app/personas/local \
    /app/personas/shared \
    /app/data/sessions

# Set working directory back to /app for runtime
WORKDIR /app

# Add entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8010

# Set environment variables (these will be overridden at runtime from .env)
ENV JWT_SECRET_KEY=change_this_in_production
ENV ADMIN_USER=admin
ENV ADMIN_PASS=password

# Run the application with custom port
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "mindroot.server", "--port", "8010"]
