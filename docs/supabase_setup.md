# AEGIS-X Supabase Setup & Production Deployment Guide

Guide for configuring Supabase Authentication, PostgreSQL database, and private Storage buckets for production deployment.

---

## 1. Create Supabase Project
1. Log into [Supabase Dashboard](https://supabase.com/dashboard) and create a new project.
2. Note down your project reference, API URL (`https://<project-ref>.supabase.co`), `anon` key, and `service_role` key.

---

## 2. Configure Private Storage Bucket
1. In Supabase Dashboard, navigate to **Storage** -> **Create a new bucket**.
2. Bucket Name: `aegis-private`
3. Toggle **Public Bucket** to **OFF** (Keep bucket strictly private).
4. Save bucket settings.

---

## 3. Apply PostgreSQL Database Migrations
1. In Supabase Dashboard, navigate to **SQL Editor**.
2. Copy the contents of [`supabase/migrations/001_initial_schema.sql`](file:///c:/Users/2403a/Documents/AEGIS-X-Product/supabase/migrations/001_initial_schema.sql).
3. Execute the migration script to create all tables (`models`, `datasets`, `reference_states`, `analyses`, `stress_tests`, `fault_tests`, `failure_memories`, `predictions`, `warnings`) and enable Row Level Security (RLS) policies.

---

## 4. Environment Variable Configuration
Configure environment variables on your production server (or in `.env`):

```bash
AEGIS_ENV=production
AUTH_REQUIRED=true
DATABASE_BACKEND=supabase
STORAGE_BACKEND=supabase

SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
SUPABASE_STORAGE_BUCKET=aegis-private

CORS_ALLOWED_ORIGINS=https://your-dashboard-domain.com
```

---

## 5. Startup Verification
Launch the FastAPI application:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Verify backend setup and readiness:
- Health check: `GET /health`
- Readiness check: `GET /ready`
- System status: `GET /api/v1/status`
- Authenticated user check: `GET /api/v1/me` (with `Authorization: Bearer <access_token>`)
