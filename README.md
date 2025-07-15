# MCP Memory System

**Persistent memory for AI assistants** - A production-ready SaaS that gives Claude Desktop and other AI tools persistent memory across conversations.

[![Production Status](https://img.shields.io/badge/status-production--ready-green)](https://mcp-memory-uw0w.onrender.com/health)
[![MCP Integration](https://img.shields.io/badge/MCP-integrated-blue)](https://modelcontextprotocol.io)

## 🚀 Quick Start

### For Users
1. **Visit**: [https://usemindmirror.com](https://usemindmirror.com) *(deploying soon)*
2. **Click**: "Inject Token" to generate your personal memory URL
3. **Copy**: The generated URL to Claude Desktop MCP settings
4. **Use**: Your AI now remembers everything across conversations!

### For Developers
```bash
# Clone and setup
git clone https://github.com/artemgetmann/mcp_memory.git
cd mcp_memory
pip install -r requirements.txt

# Start backend services
python memory_server.py      # API backend (port 8001)
python memory_mcp_direct.py  # MCP interface (port 8000)

# Start frontend (optional)
cd frontend && npm install && npm run dev  # Port 8081
```

## 🏗️ Architecture

```
User → Frontend → Backend API → PostgreSQL → MCP → Claude Desktop
```

- **Frontend**: React/TypeScript token generation interface
- **Backend**: FastAPI with PostgreSQL + pgvector storage  
- **MCP Server**: Direct SSE protocol for Claude Desktop
- **Database**: Multi-tenant with user isolation

## ✨ Key Features

### 🧠 **Intelligent Memory**
- **Semantic Search**: Find memories by meaning, not just keywords
- **Conflict Detection**: Automatically identifies contradictory preferences
- **Smart Deduplication**: Prevents storing duplicate information

### 🔒 **Multi-Tenant & Secure**
- **Token Authentication**: Each user gets a unique secure token
- **Data Isolation**: Complete separation between users
- **Memory Limits**: 25 memories per free user, unlimited for premium

### 🤖 **AI Integration**
- **Claude Desktop**: Direct MCP integration with four core functions
- **Real-time**: Instant memory storage and retrieval
- **Conflict Resolution**: AI can view and resolve memory conflicts

## 📋 API Overview

### Memory Operations
```bash
# Store a preference
POST /memories?token=YOUR_TOKEN
{"text": "I prefer working in the mornings", "tag": "preference"}

# Search memories  
POST /memories/search?token=YOUR_TOKEN
{"query": "when do I work best", "limit": 10}

# List all memories
GET /memories?token=YOUR_TOKEN
```

### User Management
```bash
# Generate new token
POST /api/generate-token
{"user_name": "Optional Name"}

# Join premium waitlist
POST /api/join-waitlist  
{"email": "user@example.com"}
```

## 🧪 Testing

```bash
# Test core functionality
python limit_test_unique.py

# Test MCP integration
npx @modelcontextprotocol/inspector "http://localhost:8000/sse?token=YOUR_TOKEN"

# Health check
curl http://localhost:8001/health
```

## 🎯 Memory Tags

Fixed set of 9 semantic categories:
- `preference` - User preferences and likes
- `habit` - Regular behaviors and routines  
- `goal` - Objectives and targets
- `constraint` - Limitations and restrictions
- `identity` - Personal identity information
- `value` - Core values and beliefs
- `project` - Work and personal projects
- `tool` - Tools and software preferences
- `routine` - Daily and weekly routines

## 🚀 Deployment

### Production (Current)
- **Backend**: Deployed on Render → [https://mcp-memory-uw0w.onrender.com](https://mcp-memory-uw0w.onrender.com)
- **Frontend**: Deploying to Vercel → `https://usemindmirror.com` *(coming soon)*
- **Database**: PostgreSQL on Supabase with pgvector

### Local Development
```bash
# Backend only
python memory_server.py && python memory_mcp_direct.py

# Full stack
./start_direct.sh  # Starts both backend services
cd frontend && npm run dev  # Start frontend
```

## 📊 System Specs

- **Response Time**: <500ms for memory operations
- **Concurrent Users**: 100+ tested successfully  
- **Memory Capacity**: 25 per free user, unlimited premium
- **Vector Model**: SentenceTransformers all-MiniLM-L6-v2 (384d)
- **Conflict Threshold**: 0.65 similarity triggers conflict detection
- **Duplicate Threshold**: 0.95 similarity blocks duplicate storage

## 🔧 Configuration

### Environment Variables
```bash
# Development
VITE_API_URL=http://localhost:8001

# Production  
VITE_API_URL=https://mcp-memory-uw0w.onrender.com
```

### Database Connection
Uses PostgreSQL with pgvector extension for vector similarity search.

## 📚 Documentation

- **Full Documentation**: See [PROJECT_DOCS.md](PROJECT_DOCS.md)
- **MCP Integration**: [Model Context Protocol](https://modelcontextprotocol.io)
- **API Reference**: See `/health` endpoint for full API docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (especially MCP integration)
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/artemgetmann/mcp_memory/issues)
- **Documentation**: [PROJECT_DOCS.md](PROJECT_DOCS.md)
- **Health Check**: [https://mcp-memory-uw0w.onrender.com/health](https://mcp-memory-uw0w.onrender.com/health)

---

**Built for the future of AI assistance** 🚀