import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { getEnvConfig } from "@/lib/config";

export const isSupabaseConfigured = (): boolean => {
  const cfg = getEnvConfig();
  return cfg.isSupabaseConfigured;
};

let clientInstance: SupabaseClient | null = null;

export const getSupabaseClient = (): SupabaseClient => {
  const cfg = getEnvConfig();
  if (cfg.isVercel && (!cfg.supabaseUrl || !cfg.supabaseAnonKey)) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY on Vercel deployment."
    );
  }

  if (!clientInstance) {
    clientInstance = createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
      },
    });
  }
  return clientInstance;
};

export const setSupabaseClientInstanceForTesting = (instance: SupabaseClient | null): void => {
  clientInstance = instance;
};

