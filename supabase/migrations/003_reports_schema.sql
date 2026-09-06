-- AEGIS-X Supabase / PostgreSQL Phase 7 Reports Schema Migration
-- Enables Row Level Security (RLS) policies linking user ownership to auth.uid()

CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    analysis_id UUID NOT NULL REFERENCES public.analyses(id) ON DELETE CASCADE,
    governance_evaluation_id UUID REFERENCES public.governance_evaluations(id) ON DELETE SET NULL,
    report_type TEXT NOT NULL,
    trust_disposition TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    report_payload_json TEXT NOT NULL,
    result_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own reports" ON public.reports;
CREATE POLICY "Users can only access their own reports" ON public.reports
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_model_id ON public.reports(model_id);
CREATE INDEX IF NOT EXISTS idx_reports_analysis_id ON public.reports(analysis_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at);
