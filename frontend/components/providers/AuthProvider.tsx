"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { setAuthToken, getValidSessionToken } from "@/lib/api";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase/client";
import { AuthSession, AuthUser } from "@/lib/supabase/types";
import { isVercelEnvironment } from "@/lib/config";

interface AuthContextType {
  user: AuthUser | null;
  session: AuthSession | null;
  loading: boolean;
  authenticated: boolean;
  isConfigured: boolean;
  signIn: (email: string, pass: string) => Promise<void>;
  signUp: (email: string, pass: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  authenticated: false,
  isConfigured: false,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const configured = isSupabaseConfigured();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(configured);

  useEffect(() => {
    if (!configured) {
      return;
    }

    const supabase = getSupabaseClient();

    const syncSessionState = async (sess: AuthSession | null) => {
      setSession(sess);
      setUser(sess?.user ?? null);
      if (sess?.access_token) {
        setAuthToken(sess.access_token);
      } else {
        const fallbackToken = await getValidSessionToken();
        if (fallbackToken) {
          const { data: latest } = await supabase.auth.getSession();
          if (latest?.session) {
            setSession(latest.session as AuthSession);
            setUser(latest.session.user as AuthUser);
            setAuthToken(latest.session.access_token);
          } else {
            setAuthToken(fallbackToken);
          }
        } else {
          setAuthToken(null);
        }
      }
      setLoading(false);
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      syncSessionState(session as AuthSession | null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      syncSessionState(session as AuthSession | null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [configured]);

  const signIn = async (email: string, pass: string) => {
    if (!configured) {
      throw new Error("Supabase Auth is not configured in current environment.");
    }
    const supabase = getSupabaseClient();
    const { data, error } = await supabase.auth.signInWithPassword({ email, password: pass });
    if (error) throw error;
    if (data.session?.access_token) {
      setAuthToken(data.session.access_token);
    }
  };

  const signUp = async (email: string, pass: string) => {
    if (!configured) {
      throw new Error("Supabase Auth is not configured in current environment.");
    }
    const supabase = getSupabaseClient();
    const { error } = await supabase.auth.signUp({ email, password: pass });
    if (error) throw error;
  };

  const signOut = async () => {
    if (configured) {
      const supabase = getSupabaseClient();
      await supabase.auth.signOut();
    }
    setSession(null);
    setUser(null);
    setAuthToken(null);
  };

  const isVercel = isVercelEnvironment();
  const authenticated = Boolean(session?.user) || (!configured && !isVercel);


  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        authenticated,
        isConfigured: configured,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
