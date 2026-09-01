# AEGIS-X Vercel Production & Preview Deployment Specification

This document defines the canonical deployment, environment variable scoping, CORS origin regex, and Supabase authentication configuration for AEGIS-X.

---

## Canonical Domains & Endpoints

| Resource | URL | Environment / Scope |
| :--- | :--- | :--- |
| **Canonical Production Frontend** | `https://aegis-x-product.vercel.app` | Production User-Facing Portal |
| **Vercel Preview Deployments** | `https://aegis-x-product-*-syedamaan70627-4156s-projects.vercel.app` | Per-PR & Branch Preview Deployments |
| **Production FastAPI Backend** | `https://aegis-x-product-production.up.railway.app/api/v1` | Railway Backend API Root |

---

## Vercel Project Environment Variable Scoping

In the Vercel Dashboard (**Project Settings -> Environment Variables**), the following environment variables **MUST be checked for BOTH Production and Preview environments**:

| Variable Name | Value | Required Scopes |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://aegis-x-product-production.up.railway.app/api/v1` | **Production + Preview** |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://kiczqwyuzjjvlmjpuuuv.supabase.co` | **Production + Preview** |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `<your_publishable_anon_key>` | **Production + Preview** |

> [!CAUTION]
> **FAIL CLOSED POLICY**: If any of these three variables is absent or placeholder on a Vercel build, AEGIS-X renders an explicit **Vercel Configuration Error** screen. It will NEVER silently fall back to `localhost`, `127.0.0.1`, `SQLITE`, or `local_dev_user`.

### FORBIDDEN Frontend Variables (NEVER add to Vercel)

- `SUPABASE_SERVICE_ROLE_KEY` *(Backend Only — Railway)*
- `DATABASE_URL` *(Backend Only — Railway)*
- Any `sb_secret_...` or service-role credential

---

## Railway CORS Configuration

In the Railway Dashboard (**Service Settings -> Environment Variables**):

| Variable Name | Value | Purpose |
| :--- | :--- | :--- |
| `CORS_ALLOWED_ORIGINS` | `https://aegis-x-product.vercel.app,http://localhost:3000` | Explicit production & local origins |
| `CORS_ALLOWED_ORIGIN_REGEX` | `^https://aegis-x-product-[a-z0-9-]+-syedamaan70627-4156s-projects\.vercel\.app$` | Project-specific Vercel preview domain family |

> [!NOTE]
> `CORSMiddleware` in FastAPI evaluates `allow_origin_regex` to safely grant CORS access to Vercel preview builds for this project without resorting to an insecure wildcard (`*`). Unrelated Vercel domains are blocked.

---

## Supabase Auth Configuration

In the Supabase Dashboard (**Authentication -> URL Configuration**):

- **Site URL**: `https://aegis-x-product.vercel.app`
- **Redirect URLs**:
  - `https://aegis-x-product.vercel.app/**`
  - `https://aegis-x-product-*-syedamaan70627-4156s-projects.vercel.app/**`
  - `http://localhost:3000/**`

---

## Route Contract & Serving Verification

- **`/`**: Next.js App Router root page (Redirects to `/dashboard` or `/login`)
- **`/login`**: AEGIS-X User Login Page (HTTP 200)
- **`/signup`**: AEGIS-X User Registration Page (HTTP 200)
- **`/dashboard`**: Protected Main Dashboard Overview (HTTP 200)
- **`/settings`**: System & Project Settings Page (HTTP 200)
