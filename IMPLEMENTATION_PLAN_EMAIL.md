# Implementation Plan: Add Email Requirement to Token Generation

**Goal:** Track user identity by requiring email when generating tokens. No authentication system - just store email with token.

Attach a required email to each new token generated via the public UI, so I can see:
- token → email → memory usage

## Changes Required:

### 1. Database Schema
Add email column to `auth_tokens` table:

```sql
ALTER TABLE auth_tokens ADD COLUMN email TEXT;
```

**Notes:**
- No `NOT NULL` constraint (existing tokens have NULL email)
- No index for now
- No UNIQUE constraint (same email can have multiple tokens)

### 2. Backend API (`memory_server.py`)

**Update TokenGenerationRequest model:**
```python
class TokenGenerationRequest(BaseModel):
    email: str  # required
    user_name: Optional[str] = None
```

**Update `generate_token()` endpoint:**
- Require email in request body
- Basic validation:
```python
if "@" not in req.email:
    raise HTTPException(status_code=400, detail="Invalid email")
```
- Store email when inserting into `auth_tokens` table
- No need to return email in response, just token as before

**Existing tokens:**
- Must continue to work as-is
- No behavior change
- Email will be NULL for old tokens

### 3. Frontend Changes

**Update TypeScript interface (`frontend/src/api/memory.ts`):**
```typescript
export interface TokenGenerationRequest {
  email: string;
  user_name?: string;
}
```

**Update UI (`frontend/src/components/TokenModal.tsx`):**
- Add email input field (required)
- Use native HTML5 validation:
```tsx
<input
  type="email"
  required
  value={email}
  onChange={...}
/>
```
- On submit, send `{ email, user_name }` to `generateToken()`

**No additional regex validation needed** - `type="email"` handles it.

## Testing Steps:
1. Generate token with valid email → succeeds, stored in DB
2. Try without email → backend returns 400
3. Verify existing tokens continue to work (no regression)

## Design Principles:
- No `NOT NULL` on email
- No index yet
- Keep validation minimal
- Don't overcomplicate migration or "auth" logic

## Files to Modify:
1. `memory_server.py` - Backend model and endpoint
2. `frontend/src/api/memory.ts` - TypeScript interface
3. `frontend/src/components/TokenModal.tsx` - UI form

---

*Created: 2025-11-18*
*Updated: 2025-11-18*
*Status: Ready for implementation*
