FROM python:3.12-slim

# Set pip to use faster mirror and disable cache to reduce build time
ENV PIP_INDEX_URL=https://pypi.org/simple/
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies and update SSL certificates
RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools
RUN pip install uv && uv tool install mcp-proxy

# Set up environment
ENV PATH="/root/.local/bin:$PATH"
ENV PORT=8000
ENV MEMORY_SERVER_PORT=8001
EXPOSE 8000

# Create app directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download the model during build to avoid runtime SSL issues
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application files
COPY memory_server.py .
COPY memory_mcp_server.py .
COPY start_services.sh .

# Make start script executable
RUN chmod +x start_services.sh

# Start both services
CMD ["./start_services.sh"]