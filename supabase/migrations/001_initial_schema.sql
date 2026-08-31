-- AEGIS-X Supabase / PostgreSQL Initial Production Schema Migration
-- Enables Row Level Security (RLS) policies linking user ownership to auth.uid()

-- 1. Models Table
CREATE TABLE IF NOT EXISTS public.models (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    predict_supported BOOLEAN NOT NULL DEFAULT TRUE,
    predict_proba_supported BOOLEAN NOT NULL DEFAULT TRUE,
    n_features_in INTEGER,
    classes_json TEXT,
    feature_names_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.models ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own models" ON public.models;
CREATE POLICY "Users can only access their own models" ON public.models
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_models_user_id ON public.models(user_id);


-- 2. Datasets Table
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    dataset_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    target_column TEXT,
    num_samples INTEGER NOT NULL,
    num_features INTEGER NOT NULL,
    feature_names_json TEXT NOT NULL,
    has_target BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own datasets" ON public.datasets;
CREATE POLICY "Users can only access their own datasets" ON public.datasets
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON public.datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_model_id ON public.datasets(model_id);


-- 3. Reference States Table
CREATE TABLE IF NOT EXISTS public.reference_states (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL UNIQUE REFERENCES public.models(id) ON DELETE CASCADE,
    dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    artifact_path TEXT NOT NULL,
    feature_names_json TEXT NOT NULL,
    num_samples INTEGER NOT NULL,
    fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.reference_states ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own reference states" ON public.reference_states;
CREATE POLICY "Users can only access their own reference states" ON public.reference_states
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_reference_states_user_id ON public.reference_states(user_id);


-- 4. Analyses Table
CREATE TABLE IF NOT EXISTS public.analyses (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    reference_dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    evaluation_dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    result_path TEXT NOT NULL,
    aggregate_ood_risk DOUBLE PRECISION,
    aggregate_uncertainty DOUBLE PRECISION,
    aggregate_drift_score DOUBLE PRECISION,
    aggregate_fused_risk DOUBLE PRECISION,
    fusion_method TEXT NOT NULL,
    has_labels BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own analyses" ON public.analyses;
CREATE POLICY "Users can only access their own analyses" ON public.analyses
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON public.analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_model_id ON public.analyses(model_id);


-- 5. Stress Tests Table
CREATE TABLE IF NOT EXISTS public.stress_tests (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    evaluation_dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    stress_type TEXT NOT NULL,
    severity DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL,
    original_risk DOUBLE PRECISION,
    stressed_risk DOUBLE PRECISION,
    risk_delta DOUBLE PRECISION,
    result_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.stress_tests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own stress tests" ON public.stress_tests;
CREATE POLICY "Users can only access their own stress tests" ON public.stress_tests
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_stress_tests_user_id ON public.stress_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_stress_tests_model_id ON public.stress_tests(model_id);


-- 6. Fault Tests Table
CREATE TABLE IF NOT EXISTS public.fault_tests (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    evaluation_dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    fault_type TEXT NOT NULL,
    severity DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL,
    result_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.fault_tests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own fault tests" ON public.fault_tests;
CREATE POLICY "Users can only access their own fault tests" ON public.fault_tests
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_fault_tests_user_id ON public.fault_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_fault_tests_model_id ON public.fault_tests(model_id);


-- 7. Failure Memories Table
CREATE TABLE IF NOT EXISTS public.failure_memories (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    n_signatures INTEGER NOT NULL,
    artifact_path TEXT NOT NULL,
    fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.failure_memories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own failure memories" ON public.failure_memories;
CREATE POLICY "Users can only access their own failure memories" ON public.failure_memories
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_failure_memories_user_id ON public.failure_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_failure_memories_model_id ON public.failure_memories(model_id);


-- 8. Predictions Table
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    horizon_steps INTEGER NOT NULL,
    mean_probability DOUBLE PRECISION,
    result_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own predictions" ON public.predictions;
CREATE POLICY "Users can only access their own predictions" ON public.predictions
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON public.predictions(model_id);


-- 9. Warnings Table
CREATE TABLE IF NOT EXISTS public.warnings (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    warning_score DOUBLE PRECISION,
    is_warning_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    threshold DOUBLE PRECISION NOT NULL,
    result_path TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.warnings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own warnings" ON public.warnings;
CREATE POLICY "Users can only access their own warnings" ON public.warnings
    FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_warnings_user_id ON public.warnings(user_id);
CREATE INDEX IF NOT EXISTS idx_warnings_model_id ON public.warnings(model_id);
