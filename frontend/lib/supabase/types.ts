import { User as SupabaseUser, Session as SupabaseSession } from "@supabase/supabase-js";

export type AuthUser = SupabaseUser;
export type AuthSession = SupabaseSession;

export interface AuthState {
  user: AuthUser | null;
  session: AuthSession | null;
  loading: boolean;
  authenticated: boolean;
}
