FROM python:3.12-slim

RUN pip install uv \
 && uv tool install mcp-proxy

# Install our memory MCP server dependencies
RUN pip install mcp httpx

ENV PATH="/root/.local/bin:$PATH"
ENV PORT=8000
EXPOSE 8000

# Copy our memory server
COPY memory_mcp_server.py .

CMD ["mcp-proxy", "--host", "0.0.0.0", "--port", "8000", "python", "memory_mcp_server.py"]