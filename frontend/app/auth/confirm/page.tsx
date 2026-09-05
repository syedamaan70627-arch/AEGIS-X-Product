"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { getSupabaseClient } from "@/lib/supabase/client";
import { classifyAuthError } from "@/lib/auth_errors";
import { LoadingState } from "@/components/ui/LoadingState";
import { CheckCircle2, AlertTriangle, RefreshCw, ShieldCheck } from "lucide-react";
import type { EmailOtpType } from "@supabase/supabase-js";

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

function AuthConfirmContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { resendVerification, isConfigured } = useAuth();

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Resend state for expired link
  const [resendEmail, setResendEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  const rawNext = searchParams ? searchParams.get("next") : null;
  const safeNext = getSanitizedReturnUrl(rawNext);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  useEffect(() => {
    if (!isConfigured) {
      // Offline local context
      setStatus("success");
      return;
    }

    const tokenHash = searchParams ? searchParams.get("token_hash") : null;
    const typeParam = searchParams ? searchParams.get("type") : null;
    const codeParam = searchParams ? searchParams.get("code") : null;

    const supabase = getSupabaseClient();

    const processVerification = async () => {
      try {
        if (tokenHash) {
          const otpType = (typeParam as EmailOtpType) || "signup";
          const { error } = await supabase.auth.verifyOtp({
            token_hash: tokenHash,
            type: otpType,
          });
          if (error) throw error;
          setStatus("success");
          return;
        }

        if (codeParam) {
          const { error } = await supabase.auth.exchangeCodeForSession(codeParam);
          if (error) throw error;
          setStatus("success");
          return;
        }

        // Check if session was already established or hash parameters were parsed by client
        const { data } = await supabase.auth.getSession();
        if (data.session) {
          setStatus("success");
          return;
        }

        // Check hash parameters if client loaded via hash redirect
        if (typeof window !== "undefined" && window.location.hash.includes("access_token")) {
          setStatus("success");
          return;
        }

        // If no token or session found, show error state
        setStatus("error");
        setErrorMessage("Verification link is missing required authentication parameters.");
      } catch (err: any) {
        const classified = classifyAuthError(err);
        setStatus("error");
        setErrorMessage(classified.message);
      }
    };

    processVerification();
  }, [searchParams, isConfigured]);

  const handleResendFromConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resendEmail || cooldown > 0 || resendLoading) return;

    setResendLoading(true);
    setResendMessage(null);
    setResendError(null);

    try {
      await resendVerification(resendEmail);
      setResendMessage("Verification email sent! Please check your inbox.");
      setCooldown(60);
    } catch (err: any) {
      const classified = classifyAuthError(err);
      setResendError(classified.message);
    } finally {
      setResendLoading(false);
    }
  };

  if (status === "verifying") {
    return (
      <div className="bg-[#151B23] border border-[#26303D] py-12 px-6 shadow-xl rounded-2xl sm:px-10 text-center font-sans">
        <LoadingState message="Verifying email address..." />
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="bg-[#151B23] border border-[#26303D] py-8 px-6 shadow-xl rounded-2xl sm:px-10 text-center space-y-6 font-sans">
        <div className="p-3 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-full w-12 h-12 mx-auto flex items-center justify-center text-[#22C55E]">
          <CheckCircle2 className="w-6 h-6" />
        </div>

        <div className="space-y-2">
          <h3 className="text-xl font-bold text-[#F3F4F6]">Email Verified Successfully</h3>
          <p className="text-xs text-[#9CA3AF] max-w-sm mx-auto leading-relaxed">
            Your AEGIS-X account is ready. Continue to Sign In to access the command center.
          </p>
        </div>

        <div className="pt-2">
          <Link
            href={`/login?next=${encodeURIComponent(safeNext)}`}
            className="inline-flex items-center justify-center w-full py-2.5 px-4 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded-lg transition-colors shadow-sm"
          >
            Continue to Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#151B23] border border-[#26303D] py-8 px-6 shadow-xl rounded-2xl sm:px-10 space-y-6 text-left font-sans">
      <div className="flex items-center space-x-3 pb-3 border-b border-[#26303D]">
        <div className="p-2.5 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl text-[#EF4444]">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-[#F3F4F6]">Verification Link Invalid or Expired</h3>
          <p className="text-[11px] text-[#9CA3AF]">The link may have expired or already been used.</p>
        </div>
      </div>

      <p className="text-xs text-[#9CA3AF] leading-relaxed">
        {errorMessage || "Request a new verification email to continue."}
      </p>

      {resendMessage && (
        <div className="p-3 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-lg text-xs text-[#22C55E]">
          {resendMessage}
        </div>
      )}

      {resendError && (
        <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-lg text-xs text-[#EF4444]">
          {resendError}
        </div>
      )}

      <form onSubmit={handleResendFromConfirm} className="space-y-3 pt-2">
        <label className="block text-xs font-semibold text-[#F3F4F6]">Request New Verification Email</label>
        <input
          type="email"
          required
          value={resendEmail}
          onChange={(e) => setResendEmail(e.target.value)}
          placeholder="Enter registered email"
          className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg px-3 py-2 text-xs text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6]"
        />
        <button
          type="submit"
          disabled={resendLoading || cooldown > 0}
          className="w-full py-2.5 px-4 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${resendLoading ? "animate-spin" : ""}`} />
          <span>
            {resendLoading
              ? "Sending..."
              : cooldown > 0
              ? `Resend Verification Email (${cooldown}s)`
              : "Resend Verification Email"}
          </span>
        </button>
      </form>

      <div className="pt-3 border-t border-[#26303D] text-center">
        <Link href="/login" className="text-xs text-[#3B82F6] font-semibold hover:underline">
          Return to Sign In
        </Link>
      </div>
    </div>
  );
}

export default function AuthConfirmPage() {
  return (
    <div className="min-h-screen bg-[#0B0F14] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans antialiased text-[#F3F4F6]">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3 mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#3B82F6] shadow-sm">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">AEGIS-X</h2>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Suspense fallback={<LoadingState message="Loading verification page..." />}>
          <AuthConfirmContent />
        </Suspense>
      </div>
    </div>
  );
}
