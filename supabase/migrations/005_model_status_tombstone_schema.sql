-- AEGIS-X Model Status & Tombstone Schema Migration
-- Safe, non-destructive forward migration adding status column to public.models

ALTER TABLE public.models ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
CREATE INDEX IF NOT EXISTS idx_models_status ON public.models(status);

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
