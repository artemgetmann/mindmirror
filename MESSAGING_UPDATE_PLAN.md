# Homepage Messaging Update Plan

**Goal:** Reposition MindMirror from "plugin for Claude/Windsurf" to "infrastructure for AI agents"

---

## Current State Analysis

**Current Hero Section** (`frontend/src/components/HeroSection.tsx`):
- Headline: "Persistent memory for Claude, Windsurf, Cursor or your own AI models"
- Subheadline: "The World's Most Advanced AI Memory System!"
- Body: "Just paste one URL and your AI will remember everything across chats..."

**Problems:**
1. ✗ Leads with vendor names (Claude, Windsurf, Cursor) = weak positioning
2. ✗ "World's Most Advanced" = marketing fluff
3. ✗ No problem statement explaining why users need this
4. ✗ "Persistent memory" = database jargon, not clear value

**What's Good:**
- ✓ "Just paste one URL" = concrete simplicity
- ✓ MCP is NOT in hero (correctly placed in Integration page)
- ✓ Integration guide explains MCP well for technical users

---

## New Messaging Structure

### Hero Section (`HeroSection.tsx` - lines 11-30)

**Headline:**
```
Long-term memory for your AI agents
```

**Subheadline:**
```
LLM APIs are stateless. MindMirror is a drop-in memory layer so your agents remember everything across chats.
```

**Supporting line:**
```
Think Postgres for your AI's long-term memory.
```

**Body (keep existing simplicity):**
```
Just paste one URL and your AI will remember everything.
No more repeating your preferences, goals, or project setup —
your AI just remembers.
```

**CTA Button:**
```
Get API Token
```

**Secondary line under CTA:**
```
25 memories free forever. Full trial coming soon.
```

**Compatibility (add below hero, separate line):**
```
Works with Claude, Cursor, Windsurf, OpenAI, and your own models.
```

---

### New Section: Problem Block

**Add this between Hero and Features sections** (new component or expand `WhyItMattersSection.tsx`):

```
The Problem
LLM APIs don't remember anything.
Every developer hacks their own storage, embeddings, and retrieval logic.

The Fix
MindMirror gives you a unified memory backend:
store, retrieve, search, and share context between agents without building infra.
```

---

## Changes Required

### 1. Update HeroSection.tsx

**File:** `/Users/user/Programming_Projects/MCP_Memory/frontend/src/components/HeroSection.tsx`

**Lines to change:**

- **Line 18-22** (Headline):
  ```tsx
  // OLD:
  Persistent memory for Claude, Windsurf, Cursor or your own AI models

  // NEW:
  Long-term memory for your AI agents
  ```

- **Line 24-26** (Subheadline):
  ```tsx
  // OLD:
  The World's Most Advanced AI Memory System!

  // NEW:
  LLM APIs are stateless. MindMirror is a drop-in memory layer so your agents remember everything across chats.
  ```

- **After line 26** (Add supporting line):
  ```tsx
  // ADD:
  <p className="text-xl text-gray-400 max-w-2xl mx-auto">
    Think Postgres for your AI's long-term memory.
  </p>
  ```

- **Line 28-30** (Body - keep as is, it's good)

- **After body copy** (Add compatibility line):
  ```tsx
  // ADD:
  <p className="text-sm text-gray-500 max-w-2xl mx-auto mt-6">
    Works with Claude, Cursor, Windsurf, OpenAI, and your own models.
  </p>
  ```

- **Line 44** (CTA button text):
  ```tsx
  // OLD:
  Generate Token

  // NEW:
  Get API Token
  ```

- **After CTA** (Add secondary line):
  ```tsx
  // ADD:
  <p className="text-sm text-gray-400 mt-3">
    25 memories free forever. Full trial coming soon.
  </p>
  ```

### 2. Create Problem Block Component (Optional)

**Option A:** Add to existing `WhyItMattersSection.tsx`

**Option B:** Create new `ProblemStatementSection.tsx` and insert between Hero and Features in `Index.tsx`

**Content:**
```tsx
<section className="py-16 bg-gray-900">
  <div className="max-w-4xl mx-auto px-4">
    <div className="grid md:grid-cols-2 gap-12">
      <div>
        <h3 className="text-2xl font-bold text-red-400 mb-4">The Problem</h3>
        <p className="text-gray-300 text-lg leading-relaxed">
          LLM APIs don't remember anything.<br/>
          Every developer hacks their own storage, embeddings, and retrieval logic.
        </p>
      </div>
      <div>
        <h3 className="text-2xl font-bold text-green-400 mb-4">The Fix</h3>
        <p className="text-gray-300 text-lg leading-relaxed">
          MindMirror gives you a unified memory backend:
          store, retrieve, search, and share context between agents without building infra.
        </p>
      </div>
    </div>
  </div>
</section>
```

### 3. Update FeaturesSection.tsx (Minor)

**File:** `/Users/user/Programming_Projects/MCP_Memory/frontend/src/components/FeaturesSection.tsx`

**Line 82** (Speed claim):
```tsx
// OLD:
Fast embedding search

// NEW:
Embedding search
```
(Remove "Fast" since we haven't measured speed)

### 4. MCP Placement (No Changes Needed)

**Current placement is correct:**
- ✓ MCP NOT mentioned in hero (good - don't confuse non-technical users)
- ✓ MCP explained in Integration page for developers
- ✓ About page mentions "MCP protocol" in technical context

**No action required for MCP placement.**

---

## Design Principles

1. **Lead with category** ("Long-term memory for AI agents"), not vendors
2. **Problem → Solution** structure (stateless APIs → memory layer)
3. **Developer positioning** ("Think Postgres") - infrastructure, not plugin
4. **Simplicity in hero** - keep "paste one URL" messaging
5. **Technical depth in secondary pages** - Integration guide covers MCP
6. **No speed claims** we can't measure (removed "fast")
7. **No marketing fluff** ("World's Most Advanced" removed)

---

## Testing Checklist

After implementation:
1. [ ] Hero headline no longer leads with vendor names
2. [ ] Subheadline explains the problem (stateless APIs)
3. [ ] "Think Postgres" line appears prominently
4. [ ] Compatibility moved below fold or to separate line
5. [ ] Problem block section exists between Hero and Features
6. [ ] CTA says "Get API Token" not "Generate Token"
7. [ ] Free tier messaging visible ("25 memories free forever")
8. [ ] MCP still explained in Integration page (not in hero)
9. [ ] No unsubstantiated claims (removed "fast", "most advanced")

---

## Files to Modify

1. `/Users/user/Programming_Projects/MCP_Memory/frontend/src/components/HeroSection.tsx` - Main changes
2. `/Users/user/Programming_Projects/MCP_Memory/frontend/src/components/FeaturesSection.tsx` - Remove "fast" claim
3. `/Users/user/Programming_Projects/MCP_Memory/frontend/src/pages/Index.tsx` - Add Problem block component (optional)
4. Create `/Users/user/Programming_Projects/MCP_Memory/frontend/src/components/ProblemStatementSection.tsx` (optional new component)

---

## Key Decisions Made

**"Long-term memory" vs "Persistent memory":**
- ✓ Use "Long-term memory" (clearer, less jargon)

**"Postgres" vs "AWS" analogy:**
- ✓ Use "Postgres" (concrete, developers understand immediately)

**MCP placement:**
- ✓ Keep MCP out of hero (current placement in Integration page is correct)

**Speed claims:**
- ✓ Remove "fast" (can't claim what we haven't measured)

**"hosted or self-hosted":**
- ✓ MindMirror is hosted-only (don't mention self-hosting)

---

*Created: 2025-11-18*
*Status: Ready for implementation*
*Estimated time: 30-45 minutes*
