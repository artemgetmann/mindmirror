# syntax=docker/dockerfile:1.2
FROM python:3.12-slim

# Set pip to use faster mirror and disable cache to reduce build time
ENV PIP_INDEX_URL=https://pypi.org/simple/
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies and update SSL certificates
RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    net-tools \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up environment
ENV PORT=8000
ENV MEMORY_SERVER_PORT=8001
EXPOSE 8000

# Create app directory
WORKDIR /app

# Copy requirements first (changes less frequently)
COPY requirements.txt .

# Install dependencies in separate layer (heavy, cached)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the model during build (heavy, cached)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application files last (changes most frequently)
COPY memory_server.py .
COPY memory_mcp_direct.py .
COPY start_direct.sh .

# Make start script executable
RUN chmod +x start_direct.sh

# Start both services with the new direct approach
CMD ["./start_direct.sh"]