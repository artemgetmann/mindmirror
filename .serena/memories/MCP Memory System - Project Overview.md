# MCP Memory System - Production SaaS

**Architecture**: Multi-tenant persistent memory system for AI assistants via Model Context Protocol (MCP)

**Tech Stack**:
- **Backend**: FastAPI + PostgreSQL (Supabase) + pgvector for vector similarity
- **Frontend**: React/TypeScript + Vite + shadcn/ui + TailwindCSS  
- **MCP**: Direct SSE implementation for Claude Desktop integration
- **Embeddings**: SentenceTransformers all-MiniLM-L6-v2 (384 dimensions)

**Production URLs**:
- Backend: https://memory.usemindmirror.com
- Frontend: https://usemindmirror.com
- Deployment: Backend on Render, Frontend on Vercel

**Key Features**:
- Token-based multi-tenant authentication
- Vector similarity search with conflict detection (>0.65 similarity)
- Memory limits: 25 per free user, unlimited for admin
- Six MCP functions: remember, recall, forget, what_do_you_know, checkpoint, resume