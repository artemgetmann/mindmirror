# Code Style & Architecture

**Python Backend**:
- FastAPI with async/await patterns
- Pydantic models for request/response validation
- PostgreSQL with psycopg2-binary for database ops
- Structured logging with timestamps
- Token-based authentication via URL parameters

**Frontend**:
- TypeScript with strict typing
- React functional components with hooks
- shadcn/ui component library (Radix UI primitives)
- TailwindCSS for styling with custom design system
- React Query for API state management
- React Router for navigation

**Key Files**:
- `memory_server.py` - Main FastAPI backend
- `memory_mcp_direct.py` - MCP protocol server  
- `frontend/src/api/memory.ts` - API client
- `frontend/src/components/TokenModal.tsx` - Token generation UI
- `CLAUDE.md` - Quick reference for AI assistants
- `DOCS.md` - Comprehensive documentation