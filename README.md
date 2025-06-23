# Memory System v0

Minimal viable memory system with vector search and fixed tags.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python memory_server.py

# Test in another terminal
python test_client.py
```

## API Endpoints

- `POST /memories` - Store memory
- `POST /memories/search` - Search memories  
- `GET /memories` - List all memories
- `GET /health` - Health check

## Test Case

The MVP test stores "Prefers blunt, fast communication" and retrieves it via search query "What do you know about my communication style?"

Must pass 10 consecutive roundtrips to validate the system.

## Tags

Fixed set: `goal`, `routine`, `preference`, `constraint`, `habit`, `project`, `tool`, `identity`, `value`