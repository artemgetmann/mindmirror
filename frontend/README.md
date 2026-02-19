# Frontend

React + Vite frontend for token generation and integration instructions.

## Setup

```bash
cp .env.example .env
npm install
npm run dev
```

## Required Env Vars

- `VITE_API_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`

## Build

```bash
npm run build
```

## Hosting

This frontend is currently hosted at:
- https://usemindmirror.com

To self-host:

1. Build assets:
```bash
npm run build
```
2. Deploy `dist/` to any static host (Vercel, Netlify, Cloudflare Pages, S3+CloudFront).
3. Set runtime env vars in your host build settings:
- `VITE_API_URL` (your backend URL, e.g. `https://memory.usemindmirror.com`)
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
