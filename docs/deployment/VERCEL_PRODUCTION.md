# AEGIS-X Vercel Production Deployment Specification

This document defines the exact production configuration contract for deploying the AEGIS-X frontend to Vercel.

---

## Project & Framework Settings

| Setting | Required Value | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | `Next.js` | Specified explicitly in `frontend/vercel.json` |
| **Root Directory** | `frontend` | Sets working context to the Next.js App Router |
| **Build Command** | `npm run build` *(or Vercel default)* | Next.js production build (`next build`) |
| **Install Command** | `npm install` *(or Vercel default)* | Installs frontend dependencies |
| **Output Directory** | *(Default / Empty)* | **DO NOT** manually configure `.next`, `out`, or `dist` |

---

## Environment Variables

### Required Public Browser Variables (Set in Vercel UI)

| Variable Name | Production Value Example | Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://kiczqwyuzjjvlmjpuuuv.supabase.co` | Supabase Auth & Public Client Endpoint |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `<your_publishable_anon_key>` | Supabase Public Publishable Anon Key |
| `NEXT_PUBLIC_API_BASE_URL` | `https://aegis-x-api.up.railway.app/api/v1` | Production FastAPI Backend Endpoint |

### FORBIDDEN Frontend Variables (NEVER add to Vercel)

- `SUPABASE_SERVICE_ROLE_KEY` *(Backend Only — Railway)*
- `DATABASE_URL` *(Backend Only — Railway)*
- Any `sb_secret_...` or service-role credential

---

## Route Contract & Serving Verification

- **`/`**: Next.js App Router root page (Redirects to `/dashboard` or `/login`)
- **`/login`**: AEGIS-X User Login Page (HTTP 200)
- **`/signup`**: AEGIS-X User Registration Page (HTTP 200)
- **`/dashboard`**: Protected Main Dashboard Overview (HTTP 200)
- **`/settings`**: System & Project Settings Page (HTTP 200)
