-- AEGIS-X Supabase / PostgreSQL Phase 7 Reports Schema Production Repair Migration
-- Safe, non-destructive forward migration establishing canonical public.reports table

CREATE TABLE IF NOT EXISTS public.reports (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    analysis_id TEXT NOT NULL,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    disposition TEXT NOT NULL,
    completeness_score DOUBLE PRECISION NOT NULL,
    result_path TEXT NOT NULL,
    snapshot_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure correct RLS and Ownership Policy
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can only access their own reports" ON public.reports;
DROP POLICY IF EXISTS "reports_owner_policy" ON public.reports;

CREATE POLICY "Users can only access their own reports" ON public.reports
    FOR ALL USING (auth.uid()::text = user_id);

-- Create Required Indexes
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_model_id ON public.reports(model_id);
CREATE INDEX IF NOT EXISTS idx_reports_analysis_id ON public.reports(analysis_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at DESC);

-- Grants & Revokes
REVOKE ALL ON TABLE public.reports FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.reports TO authenticated;

-- Force PostgREST schema cache reload
NOTIFY pgrst, 'reload schema';

