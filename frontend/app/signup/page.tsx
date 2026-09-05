"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { classifyAuthError, maskEmail } from "@/lib/auth_errors";
import { ErrorState } from "@/components/ui/ErrorState";
import { CheckCircle2, Eye, EyeOff, Lock, Mail, RefreshCw, ShieldCheck } from "lucide-react";

export default function SignUpPage() {
  const router = useRouter();
  const { signUp, resendVerification, isConfigured } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorDetails, setErrorDetails] = useState<{ title?: string; message: string } | null>(null);
  const [submitted, setSubmitted] = useState(false);

  // Resend state & 60s cooldown
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !confirmPassword) {
      setErrorDetails({ title: "Form Incomplete", message: "Please complete all required fields." });
      return;
    }
    if (password.length < 8) {
      setErrorDetails({ title: "Password Requirements Unmet", message: "Password must be at least 8 characters long." });
      return;
    }
    if (password !== confirmPassword) {
      setErrorDetails({ title: "Password Mismatch", message: "Passwords do not match." });
      return;
    }

    setLoading(true);
    setErrorDetails(null);
    try {
      if (!isConfigured) {
        router.push("/dashboard");
        return;
      }
      await signUp(email, password);
      setSubmitted(true);
    } catch (err: any) {
      const classified = classifyAuthError(err);
      setErrorDetails({ title: classified.title, message: classified.message });
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resendLoading) return;
    setResendLoading(true);
    setResendMessage(null);
    setResendError(null);

    try {
      await resendVerification(email);
      setResendMessage("Verification email sent! Please check your inbox and spam folder.");
      setCooldown(60);
    } catch (err: any) {
      const classified = classifyAuthError(err);
      setResendError(classified.message);
    } finally {
      setResendLoading(false);
    }
  };

  const handleResetForm = () => {
    setSubmitted(false);
    setErrorDetails(null);
    setResendMessage(null);
    setResendError(null);
    setPassword("");
    setConfirmPassword("");
  };

  return (
    <div className="min-h-screen bg-[#0B0F14] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans antialiased text-[#F3F4F6]">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#3B82F6] shadow-sm mb-2">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#F3F4F6] font-sans">Create AEGIS-X Account</h2>
        <p className="text-xs text-[#9CA3AF] max-w-xs mx-auto leading-relaxed font-sans">
          Register an account for AEGIS-X reliability telemetry, failure warning, and model evaluations
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md font-sans">
        <div className="bg-[#151B23] border border-[#26303D] py-8 px-6 shadow-xl rounded-2xl sm:px-10 space-y-6">
          {submitted ? (
            <div className="space-y-5 text-left font-sans">
              <div className="flex items-center space-x-3 pb-2 border-b border-[#26303D]">
                <div className="p-2 bg-[#3B82F6]/10 border border-[#3B82F6]/30 rounded-lg text-[#3B82F6]">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#F3F4F6] font-sans">Check Your Email</h3>
                  <p className="text-[11px] text-[#9CA3AF]">Verification email sent to registration address</p>
                </div>
              </div>

              <div className="p-3.5 bg-[#0F141B] border border-[#26303D] rounded-xl space-y-2">
                <p className="text-xs text-[#E5E7EB] leading-relaxed">
                  We sent a verification link to <span className="font-semibold text-[#3B82F6] font-mono">{maskEmail(email)}</span>. Verify your email address before signing in to AEGIS-X.
                </p>
              </div>

              <div className="space-y-2 text-xs text-[#9CA3AF]">
                <p className="font-semibold text-[#F3F4F6]">Instructions:</p>
                <ul className="list-disc pl-5 space-y-1 text-[11px] leading-relaxed">
                  <li>Check your inbox and spam folder.</li>
                  <li>Open the verification email.</li>
                  <li>Select “Confirm email address.”</li>
                  <li>Return to AEGIS-X and sign in.</li>
                </ul>
              </div>

              {resendMessage && (
                <div className="p-3 bg-[#22C55E]/10 border border-[#22C55E]/30 rounded-lg text-xs text-[#22C55E] flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{resendMessage}</span>
                </div>
              )}

              {resendError && (
                <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-lg text-xs text-[#EF4444]">
                  {resendError}
                </div>
              )}

              <div className="pt-2 space-y-2.5">
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resendLoading || cooldown > 0}
                  className="w-full py-2.5 px-4 bg-[#26303D] hover:bg-[#323F50] text-[#F3F4F6] font-semibold text-xs rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
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

                <div className="grid grid-cols-2 gap-2">
                  <Link
                    href="/login"
                    className="w-full py-2 px-3 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded-lg text-center transition-colors shadow-sm"
                  >
                    Return to Sign In
                  </Link>
                  <button
                    type="button"
                    onClick={handleResetForm}
                    className="w-full py-2 px-3 bg-transparent border border-[#26303D] hover:bg-[#0F141B] text-[#9CA3AF] hover:text-[#F3F4F6] font-medium text-xs rounded-lg transition-colors"
                  >
                    Use a Different Email
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <>
              {errorDetails && (
                <ErrorState title={errorDetails.title} message={errorDetails.message} />
              )}

              <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Work Email Address *</label>
                  <div className="relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#6B7280]">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="analyst@enterprise.io"
                      className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg pl-10 pr-3 py-2.5 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] transition-all font-sans"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Password (Min 8 chars) *</label>
                  <div className="relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#6B7280]">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg pl-10 pr-10 py-2.5 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] transition-all font-sans"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#6B7280] hover:text-[#9CA3AF]"
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-[#F3F4F6] mb-1 font-sans">Confirm Password *</label>
                  <div className="relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#6B7280]">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg pl-10 pr-10 py-2.5 text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] transition-all font-sans"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold font-sans rounded-lg shadow-sm transition-all disabled:opacity-50 mt-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
                >
                  {loading ? "Creating Account..." : "Create Account"}
                </button>
              </form>

              <div className="pt-4 border-t border-[#26303D] text-center text-xs text-[#9CA3AF] font-sans">
                Already have an account?{" "}
                <Link href="/login" className="text-[#3B82F6] font-semibold hover:underline">
                  Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}


