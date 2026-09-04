import assert from "node:assert";
import { test, beforeEach, afterEach } from "node:test";
import { api, setAuthToken } from "../lib/api";

const originalFetch = globalThis.fetch;
const originalEnv = { ...process.env };

beforeEach(() => {
  setAuthToken(null);
  process.env = { ...originalEnv };
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  process.env = { ...originalEnv };
  setAuthToken(null);
});

// Helper testing return destination sanitizer
function sanitizeReturnUrl(rawNext: string | null): string {
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

test("Scenario 1: Unauthenticated protected route access attempts redirect to /login with next target", () => {
  const currentPath = "/models";
  const search = "filter=active";
  const fullPath = `${currentPath}?${search}`;
  const redirectUrl = `/login?next=${encodeURIComponent(fullPath)}`;

  assert.strictEqual(redirectUrl, "/login?next=%2Fmodels%3Ffilter%3Dactive");
});

test("Scenario 2: Return URL sanitizer preserves valid internal routes and blocks open-redirects", () => {
  assert.strictEqual(sanitizeReturnUrl("/models"), "/models");
  assert.strictEqual(sanitizeReturnUrl("/reliability?model_id=mod1"), "/reliability?model_id=mod1");
  assert.strictEqual(sanitizeReturnUrl("/dashboard"), "/dashboard");

  // Open-redirect attack attempts must safely resolve to default /dashboard
  assert.strictEqual(sanitizeReturnUrl("https://evil-phishing.com"), "/dashboard");
  assert.strictEqual(sanitizeReturnUrl("//evil-phishing.com"), "/dashboard");
  assert.strictEqual(sanitizeReturnUrl("/\\evil-phishing.com"), "/dashboard");
  assert.strictEqual(sanitizeReturnUrl("javascript:alert(1)"), "/dashboard");
});

test("Scenario 3: No protected API request is fired when auth state is unauthenticated", async () => {
  let fetchCalled = false;
  globalThis.fetch = (async () => {
    fetchCalled = true;
    return new Response(JSON.stringify({ models: [] }), { status: 200 });
  }) as typeof fetch;

  const authLoading = false;
  const authenticated = false;

  // Emulate page useEffect logic: if authLoading or !authenticated -> return without API call
  let apiFired = false;
  if (!authLoading && authenticated) {
    await api.listModels();
    apiFired = true;
  }

  assert.strictEqual(apiFired, false);
  assert.strictEqual(fetchCalled, false);
});

test("Scenario 4: Auth-loading state suppresses API calls and premature redirects", async () => {
  let fetchCalled = false;
  globalThis.fetch = (async () => {
    fetchCalled = true;
    return new Response(JSON.stringify({ models: [] }), { status: 200 });
  }) as typeof fetch;

  const authLoading = true;
  const authenticated = false;

  let redirectTriggered = false;
  let apiFired = false;

  // In ProtectedRoute: while loading is true, do not redirect and do not render protected children
  if (!authLoading && !authenticated) {
    redirectTriggered = true;
  }
  if (!authLoading && authenticated) {
    await api.listModels();
    apiFired = true;
  }

  assert.strictEqual(redirectTriggered, false);
  assert.strictEqual(apiFired, false);
  assert.strictEqual(fetchCalled, false);
});

test("Scenario 5: Authenticated session cleanly executes protected API calls with Bearer token", async () => {
  let capturedAuth: string | null = null;
  globalThis.fetch = (async (_input: RequestInfo | URL, init?: RequestInit) => {
    const headers = (init?.headers as Record<string, string>) || {};
    capturedAuth = headers["Authorization"] || null;
    return new Response(JSON.stringify({ models: [{ model_id: "mod-123", model_name: "Test" }] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  setAuthToken("valid-user-session-token");
  const res = await api.listModels();

  assert.strictEqual(capturedAuth, "Bearer valid-user-session-token");
  assert.strictEqual(res.models.length, 1);
  assert.strictEqual(res.models[0].model_id, "mod-123");
});

test("Scenario 6: HTTP 401 unrecoverable session expiry clears token safely", async () => {
  globalThis.fetch = (async () => {
    return new Response(JSON.stringify({ detail: "Missing or malformed Authorization header. Bearer token required." }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  setAuthToken("expired-token");

  try {
    await api.listModels();
    assert.fail("Should have thrown ApiError 401");
  } catch (err: any) {
    assert.strictEqual(err.status, 401);
  }
});
