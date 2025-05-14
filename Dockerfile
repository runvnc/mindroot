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

# Copy project files
COPY . /app/

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

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8010

# Set environment variables (these should be overridden at runtime)
ENV JWT_SECRET_KEY=change_this_in_production

# Run the application with custom port
CMD ["python", "-m", "mindroot.server", "--port", "8010"]
