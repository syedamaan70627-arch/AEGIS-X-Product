import assert from "node:assert";
import { test, beforeEach, afterEach } from "node:test";
import { api, getApiServerRoot, setAuthToken, getValidSessionToken } from "../lib/api";
import { setStoredAuthToken, getStoredAuthToken } from "../lib/auth";
import { setSupabaseClientInstanceForTesting } from "../lib/supabase/client";

const originalFetch = globalThis.fetch;
const originalEnv = { ...process.env };

beforeEach(() => {
  setAuthToken(null);
  setSupabaseClientInstanceForTesting(null);
  process.env = { ...originalEnv };
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  setSupabaseClientInstanceForTesting(null);
  process.env = { ...originalEnv };
  setAuthToken(null);
});

test("Scenario 1: Current Supabase access token is attached to protected request", async () => {
  let capturedAuthorization: string | null = null;
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = (init?.headers as Record<string, string>) || {};
    capturedAuthorization = headers["Authorization"] || null;
    return new Response(JSON.stringify({ models: [] }), { status: 200, headers: { "Content-Type": "application/json" } });
  }) as typeof fetch;

  setAuthToken("supabase-valid-token-111");
  await api.listModels();
  assert.strictEqual(capturedAuthorization, "Bearer supabase-valid-token-111");
});

test("Scenario 2: Stale legacy token cannot override current Supabase access token", async () => {
  setStoredAuthToken("stale-legacy-token-999");
  setAuthToken("fresh-supabase-token-222");

  let capturedAuthorization: string | null = null;
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = (init?.headers as Record<string, string>) || {};
    capturedAuthorization = headers["Authorization"] || null;
    return new Response(JSON.stringify({ user_id: "user-123", email: "user@test.com", authenticated: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  await api.getUserMe();
  assert.strictEqual(capturedAuthorization, "Bearer fresh-supabase-token-222");
  assert.notStrictEqual(capturedAuthorization, "Bearer stale-legacy-token-999");
});

test("Scenario 3: Initial session restoration works", async () => {
  setAuthToken("restored-session-token-333");
  const token = await getValidSessionToken();
  assert.strictEqual(token, "restored-session-token-333");
});

test("Scenario 4: Token refresh updates API Authorization", async () => {
  setAuthToken("initial-token-444");
  let capturedAuth: string | null = null;

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = (init?.headers as Record<string, string>) || {};
    capturedAuth = headers["Authorization"] || null;
    return new Response(JSON.stringify({ models: [] }), { status: 200 });
  }) as typeof fetch;

  await api.listModels();
  assert.strictEqual(capturedAuth, "Bearer initial-token-444");

  setAuthToken("refreshed-token-444-new");
  await api.listModels();
  assert.strictEqual(capturedAuth, "Bearer refreshed-token-444-new");
});

test("Scenario 5 & 6: HTTP 401 triggers one refresh attempt & succeeds with refreshed token", async () => {
  let callCount = 0;
  const authHeadersSent: string[] = [];

  process.env.NEXT_PUBLIC_SUPABASE_URL = "https://mock.supabase.co";
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "mock-anon-key";

  const mockSupabase = {
    auth: {
      getSession: async () => ({ data: { session: { access_token: "old-expired-token-555" } } }),
      refreshSession: async () => ({
        data: { session: { access_token: "new-refreshed-token-666" } },
        error: null,
      }),
    },
  };
  setSupabaseClientInstanceForTesting(mockSupabase as any);

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    callCount++;
    const headers = (init?.headers as Record<string, string>) || {};
    authHeadersSent.push(headers["Authorization"] || "");
    if (callCount === 1) {
      return new Response(JSON.stringify({ detail: "Invalid or expired access token." }), { status: 401 });
    }
    return new Response(JSON.stringify({ models: [{ model_id: "m1", model_name: "Test" }] }), { status: 200 });
  }) as typeof fetch;

  const result = await api.listModels();
  assert.strictEqual(callCount, 2);
  assert.strictEqual(authHeadersSent[0], "Bearer old-expired-token-555");
  assert.strictEqual(authHeadersSent[1], "Bearer new-refreshed-token-666");
  assert.strictEqual(result.models.length, 1);
});

test("Scenario 7: Refresh failure does not loop infinitely", async () => {
  let callCount = 0;

  process.env.NEXT_PUBLIC_SUPABASE_URL = "https://mock.supabase.co";
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "mock-anon-key";

  const mockSupabase = {
    auth: {
      getSession: async () => ({ data: { session: null } }),
      refreshSession: async () => ({ data: { session: null }, error: new Error("Refresh failed") }),
    },
  };
  setSupabaseClientInstanceForTesting(mockSupabase as any);

  globalThis.fetch = (async () => {
    callCount++;
    return new Response(JSON.stringify({ detail: "Invalid or expired access token." }), { status: 401 });
  }) as typeof fetch;

  await assert.rejects(async () => {
    await api.listModels();
  }, (err: any) => {
    assert.strictEqual(err.status, 401);
    return true;
  });
  // Must only attempt original request + 1 refresh check, no infinite loops
  assert.strictEqual(callCount, 1);
  assert.strictEqual(getStoredAuthToken(), null);
});

test("Scenario 8: Sign out clears auth state", async () => {
  setAuthToken("active-token-888");
  setStoredAuthToken("active-token-888");

  setAuthToken(null);
  assert.strictEqual(getStoredAuthToken(), null);
});

test("Scenario 9: Protected request without session fails safely", async () => {
  globalThis.fetch = (async () => {
    return new Response(JSON.stringify({ detail: "Missing or malformed Authorization header." }), { status: 401 });
  }) as typeof fetch;

  await assert.rejects(async () => {
    await api.getUserMe();
  }, (err: any) => {
    assert.strictEqual(err.status, 401);
    return true;
  });
});

test("Scenario 10: Health and readiness use production-derived API root, not localhost", async () => {
  process.env.NEXT_PUBLIC_API_BASE_URL = "https://aegis-x-product-production.up.railway.app/api/v1";

  const derivedRoot = getApiServerRoot();
  assert.strictEqual(derivedRoot, "https://aegis-x-product-production.up.railway.app");

  let fetchedHealthUrl = "";
  let fetchedReadyUrl = "";

  globalThis.fetch = (async (input: RequestInfo | URL) => {
    const urlStr = input.toString();
    if (urlStr.includes("health")) fetchedHealthUrl = urlStr;
    if (urlStr.includes("ready")) fetchedReadyUrl = urlStr;
    return new Response(JSON.stringify({ status: "healthy" }), { status: 200 });
  }) as typeof fetch;

  await api.getHealth();
  await api.getReadiness();

  assert.strictEqual(fetchedHealthUrl, "https://aegis-x-product-production.up.railway.app/health");
  assert.strictEqual(fetchedReadyUrl, "https://aegis-x-product-production.up.railway.app/ready");
  assert.ok(!fetchedHealthUrl.includes("127.0.0.1:8000"));
  assert.ok(!fetchedReadyUrl.includes("127.0.0.1:8000"));
});
