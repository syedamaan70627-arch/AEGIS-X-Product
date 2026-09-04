"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Eye, EyeOff, Lock, Mail, ShieldCheck } from "lucide-react";

function getSanitizedReturnUrl(rawNext: string | null): string {
  if (!rawNext) return "/dashboard";
  if (
    rawNext.startsWith("/") &&
    !rawNext.startsWith("//") &&
    !rawNext.startsWith("/\\") &&
    !rawNext.includes(":")
  ) {
    return rawNext;
  }
  return "/dashboard";
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signIn, authenticated, isConfigured, loading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nextParam = searchParams ? searchParams.get("next") : null;
  const targetUrl = getSanitizedReturnUrl(nextParam);

  useEffect(() => {
    if (!authLoading && authenticated) {
      router.replace(targetUrl);
    }
  }, [authLoading, authenticated, targetUrl, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      if (!isConfigured) {
        // Offline local mode fallback
        router.push(targetUrl);
        return;
      }
      await signIn(email, password);
      router.push(targetUrl);
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800/80 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 space-y-6 backdrop-blur-md">
      {!isConfigured && (
        <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-300 space-y-1">
          <span className="font-bold font-mono uppercase block text-[11px] text-amber-400">Offline Local Context</span>
          <p className="text-[11px] text-amber-200/90 leading-normal">
            Supabase auth credentials are not configured. Click sign in to open local development session.
          </p>
        </div>
      )}

      {error && <ErrorState message={error} />}

      <form onSubmit={handleSubmit} className="space-y-5 text-xs">
        <div>
          <label className="block font-semibold text-slate-300 mb-1.5">Work Email Address</label>
          <div className="relative rounded-lg shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@enterprise.io"
              className="w-full bg-slate-950 border border-slate-800/80 rounded-lg pl-10 pr-3 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-mono"
            />
          </div>
        </div>

        <div>
          <label className="block font-semibold text-slate-300 mb-1.5">Password</label>
          <div className="relative rounded-lg shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full bg-slate-950 border border-slate-800/80 rounded-lg pl-10 pr-10 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-mono"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
              aria-label="Toggle password visibility"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow-md transition-all disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {loading ? "Authenticating Session..." : "Sign In to Command Center"}
        </button>
      </form>

      {isConfigured && (
        <div className="pt-4 border-t border-slate-800/80 text-center text-xs text-slate-400">
          Need an enterprise account?{" "}
          <Link href="/signup" className="text-cyan-400 font-semibold hover:text-cyan-300">
            Create Account
          </Link>
        </div>
      )}
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans antialiased text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-xl shadow-indigo-950/80 ring-1 ring-white/10 mb-2">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100">AEGIS-X</h2>
        <p className="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
          Model-Agnostic Enterprise Framework for AI Reliability Monitoring, Stress Testing & Early Warning
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Suspense fallback={<LoadingState message="Loading login screen..." />}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
