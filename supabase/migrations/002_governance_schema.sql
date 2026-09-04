-- AEGIS-X Supabase / PostgreSQL Phase 6 Governance Schema Migration
-- Enables Row Level Security (RLS) policies linking user ownership to auth.uid()

-- 1. Governance Evaluations Table
CREATE TABLE IF NOT EXISTS public.governance_evaluations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES public.analyses(id) ON DELETE SET NULL,
    decision_id TEXT NOT NULL,
    state_index INTEGER NOT NULL,
    operating_mode TEXT NOT NULL,
    raw_action TEXT NOT NULL,
    effective_action TEXT NOT NULL,
    previous_effective_action TEXT,
    transition_occurred BOOLEAN NOT NULL DEFAULT FALSE,
    transition_reason TEXT,
    p_adverse DOUBLE PRECISION,
    prediction_set_json TEXT,
    reason_codes_json TEXT,
    calibrated BOOLEAN NOT NULL DEFAULT FALSE,
    calibrator_artifact_id TEXT,
    calibrator_artifact_sha256 TEXT,
    evidence_snapshot_hash TEXT NOT NULL,
    result_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.governance_evaluations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own governance evaluations" ON public.governance_evaluations;
CREATE POLICY "Users can only access their own governance evaluations" ON public.governance_evaluations
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_gov_eval_user_id ON public.governance_evaluations(user_id);
CREATE INDEX IF NOT EXISTS idx_gov_eval_model_id ON public.governance_evaluations(model_id);
CREATE INDEX IF NOT EXISTS idx_gov_eval_created_at ON public.governance_evaluations(created_at);


-- 2. Governance Transitions Audit Log Table
CREATE TABLE IF NOT EXISTS public.governance_transitions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES public.governance_evaluations(id) ON DELETE CASCADE,
    state_index INTEGER NOT NULL,
    previous_state TEXT,
    new_state TEXT NOT NULL,
    raw_action TEXT NOT NULL,
    transition_reason TEXT NOT NULL,
    evidence_snapshot_hash TEXT NOT NULL,
    calibrated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.governance_transitions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own governance transitions" ON public.governance_transitions;
CREATE POLICY "Users can only access their own governance transitions" ON public.governance_transitions
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_gov_trans_user_id ON public.governance_transitions(user_id);
CREATE INDEX IF NOT EXISTS idx_gov_trans_model_id ON public.governance_transitions(model_id);
CREATE INDEX IF NOT EXISTS idx_gov_trans_evaluation_id ON public.governance_transitions(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_gov_trans_created_at ON public.governance_transitions(created_at);
