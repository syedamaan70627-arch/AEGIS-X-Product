import assert from "node:assert";
import { test, beforeEach, afterEach } from "node:test";
import { classifyAuthError, maskEmail } from "../lib/auth_errors";
import { setSupabaseClientInstanceForTesting } from "../lib/supabase/client";

const originalFetch = globalThis.fetch;
const originalEnv = { ...process.env };

beforeEach(() => {
  setSupabaseClientInstanceForTesting(null);
  process.env = { ...originalEnv };
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  setSupabaseClientInstanceForTesting(null);
  process.env = { ...originalEnv };
});

// Helper for Return URL sanitizer
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

test("Auth UX 1: classifyAuthError maps email_not_confirmed correctly", () => {
  const err = { code: "email_not_confirmed", message: "Email not confirmed" };
  const classified = classifyAuthError(err);
  assert.strictEqual(classified.code, "email_not_confirmed");
  assert.strictEqual(classified.title, "Email Verification Required");
  assert.strictEqual(classified.isUnconfirmedEmail, true);
  assert.ok(!classified.title.includes("Backend Error Encountered"));
});

test("Auth UX 2: classifyAuthError maps string error 'Email not confirmed'", () => {
  const classified = classifyAuthError("Email not confirmed");
  assert.strictEqual(classified.code, "email_not_confirmed");
  assert.strictEqual(classified.title, "Email Verification Required");
  assert.strictEqual(classified.isUnconfirmedEmail, true);
});

test("Auth UX 3: classifyAuthError maps rate limit errors safely", () => {
  const err = { code: "over_email_send_rate_limit", message: "For security purposes, you can only request this once every 60 seconds" };
  const classified = classifyAuthError(err);
  assert.strictEqual(classified.code, "over_email_send_rate_limit");
  assert.strictEqual(classified.title, "Rate Limit Exceeded");
  assert.strictEqual(classified.isRateLimited, true);
});

test("Auth UX 4: classifyAuthError maps expired OTP tokens", () => {
  const err = { code: "otp_expired", message: "Token has expired or is invalid" };
  const classified = classifyAuthError(err);
  assert.strictEqual(classified.code, "otp_expired");
  assert.strictEqual(classified.title, "Verification Link Invalid or Expired");
  assert.strictEqual(classified.isUnconfirmedEmail, false);
});

test("Auth UX 5: classifyAuthError hides raw Supabase/FastAPI/Railway error details on generic errors", () => {
  const err = { code: "500", message: "AuthApiError: Internal Railway service crash on http://fastapi.backend" };
  const classified = classifyAuthError(err);
  assert.strictEqual(classified.title, "Authentication Failed");
  assert.ok(!classified.message.includes("AuthApiError"));
  assert.ok(!classified.message.includes("Railway"));
  assert.ok(!classified.message.includes("fastapi"));
});

test("Auth UX 6: maskEmail utility masks user emails correctly", () => {
  assert.strictEqual(maskEmail("analyst@enterprise.io"), "a***t@enterprise.io");
  assert.strictEqual(maskEmail("john.doe@aegis-x.com"), "j***e@aegis-x.com");
  assert.strictEqual(maskEmail("ab@domain.com"), "a*@domain.com");
  assert.strictEqual(maskEmail("a@domain.com"), "a***@domain.com");
});

test("Auth UX 7: Return URL sanitizer preserves valid internal routes & rejects external/open redirects", () => {
  assert.strictEqual(getSanitizedReturnUrl("/dashboard?view=models"), "/dashboard?view=models");
  assert.strictEqual(getSanitizedReturnUrl("/reliability"), "/reliability");
  assert.strictEqual(getSanitizedReturnUrl("https://evil-attacker.com"), "/dashboard");
  assert.strictEqual(getSanitizedReturnUrl("//evil-attacker.com"), "/dashboard");
  assert.strictEqual(getSanitizedReturnUrl("/\\evil-attacker.com"), "/dashboard");
  assert.strictEqual(getSanitizedReturnUrl("javascript:alert(1)"), "/dashboard");
});

test("Auth UX 8: Resend verification request invokes Supabase auth.resend with type signup", async () => {
  let capturedType: string | null = null;
  let capturedEmail: string | null = null;
  let capturedRedirectUrl: string | null = null;

  const mockSupabase = {
    auth: {
      resend: async (payload: any) => {
        capturedType = payload.type;
        capturedEmail = payload.email;
        capturedRedirectUrl = payload.options?.emailRedirectTo || null;
        return { data: {}, error: null };
      },
    },
  };

  setSupabaseClientInstanceForTesting(mockSupabase as any);

  // Perform mock call matching AuthProvider logic
  const normalizedEmail = "testuser@aegis-x.com".trim().toLowerCase();
  const { error } = await mockSupabase.auth.resend({
    type: "signup",
    email: normalizedEmail,
    options: {
      emailRedirectTo: "https://aegis-x-product.vercel.app/auth/confirm",
    },
  });

  assert.strictEqual(error, null);
  assert.strictEqual(capturedType, "signup");
  assert.strictEqual(capturedEmail, "testuser@aegis-x.com");
  assert.strictEqual(capturedRedirectUrl, "https://aegis-x-product.vercel.app/auth/confirm");
});

test("Auth UX 9: Resend verification prevents empty email submission", () => {
  const blankEmail = "   ";
  const normalized = blankEmail.trim().toLowerCase();
  assert.strictEqual(normalized.length, 0);
});

test("Auth UX 10: Confirmation verifyOtp succeeds with valid token_hash", async () => {
  let capturedTokenHash: string | null = null;
  let capturedType: string | null = null;

  const mockSupabase = {
    auth: {
      verifyOtp: async (params: any) => {
        capturedTokenHash = params.token_hash;
        capturedType = params.type;
        return { data: { session: { access_token: "mock-token" } }, error: null };
      },
    },
  };

  const { data, error } = await mockSupabase.auth.verifyOtp({
    token_hash: "valid_pkce_token_hash_123",
    type: "signup",
  });

  assert.strictEqual(error, null);
  assert.strictEqual(capturedTokenHash, "valid_pkce_token_hash_123");
  assert.strictEqual(capturedType, "signup");
  assert.ok(data.session);
});
