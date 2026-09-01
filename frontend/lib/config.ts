/**
 * AEGIS-X Centralized Environment Configuration & Validation
 */

export interface EnvConfig {
  isVercel: boolean;
  vercelEnv: string | null;
  apiBaseUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
  isSupabaseConfigured: boolean;
  isValid: boolean;
  missingVars: string[];
}

export function isVercelEnvironment(): boolean {
  return (
    process.env.NEXT_PUBLIC_VERCEL_ENV !== undefined ||
    process.env.VERCEL === "1" ||
    process.env.NEXT_PUBLIC_VERCEL_URL !== undefined
  );
}

export function isPlaceholderUrl(url: string | undefined): boolean {
  if (!url) return true;
  const lower = url.toLowerCase().trim();
  return (
    lower.includes("placeholder") ||
    lower.includes("localhost") ||
    lower.includes("127.0.0.1") ||
    lower.includes("your-supabase") ||
    lower.includes("example.com")
  );
}

export function isPlaceholderKey(key: string | undefined): boolean {
  if (!key) return true;
  const lower = key.toLowerCase().trim();
  return lower.includes("placeholder") || lower.includes("your-anon-key");
}

export function getEnvConfig(): EnvConfig {
  const isVercel = isVercelEnvironment();
  const vercelEnv = process.env.NEXT_PUBLIC_VERCEL_ENV || process.env.VERCEL_ENV || null;

  const rawApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const rawSupabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const rawSupabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  const missingVars: string[] = [];

  if (!rawApiBaseUrl || (isVercel && isPlaceholderUrl(rawApiBaseUrl))) {
    missingVars.push("NEXT_PUBLIC_API_BASE_URL");
  }
  if (!rawSupabaseUrl || (isVercel && isPlaceholderUrl(rawSupabaseUrl))) {
    missingVars.push("NEXT_PUBLIC_SUPABASE_URL");
  }
  if (!rawSupabaseAnonKey || (isVercel && isPlaceholderKey(rawSupabaseAnonKey))) {
    missingVars.push("NEXT_PUBLIC_SUPABASE_ANON_KEY");
  }

  const isValid = !isVercel || missingVars.length === 0;

  // On Vercel: Fail closed! Do NOT fall back to local development values or placeholders.
  // In local development (isVercel is false): Allow local development fallbacks.
  const apiBaseUrl = rawApiBaseUrl || (isVercel ? "" : "http://127.0.0.1:8000/api/v1");
  const supabaseUrl = rawSupabaseUrl || (isVercel ? "" : "https://placeholder-project.supabase.co");
  const supabaseAnonKey = rawSupabaseAnonKey || (isVercel ? "" : "placeholder-anon-key");

  const isSupabaseConfigured = Boolean(
    rawSupabaseUrl &&
    rawSupabaseAnonKey &&
    !isPlaceholderUrl(rawSupabaseUrl) &&
    !isPlaceholderKey(rawSupabaseAnonKey)
  );

  return {
    isVercel,
    vercelEnv,
    apiBaseUrl,
    supabaseUrl,
    supabaseAnonKey,
    isSupabaseConfigured,
    isValid,
    missingVars,
  };
}

export function validateVercelConfig(): void {
  const config = getEnvConfig();
  if (config.isVercel && !config.isValid) {
    throw new Error(
      `[Vercel Deployment Config Error] Missing required production environment variables: ${config.missingVars.join(
        ", "
      )}. On Vercel, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, and NEXT_PUBLIC_API_BASE_URL must be configured.`
    );
  }
}
