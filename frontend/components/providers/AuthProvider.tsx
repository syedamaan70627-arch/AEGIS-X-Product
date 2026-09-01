"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { setAuthToken } from "@/lib/api";
import { getStoredAuthToken, setStoredAuthToken } from "@/lib/auth";
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
  const [user, setUser] = useState<AuthUser | null>(null);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(true);
  const configured = isSupabaseConfigured();

  useEffect(() => {
    if (!configured) {
      setLoading(false);
      return;
    }

    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.access_token) {
        setAuthToken(session.access_token);
      } else {
        setAuthToken(null);
      }
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.access_token) {
        setAuthToken(session.access_token);
      } else {
        setAuthToken(null);
      }
      setLoading(false);
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
