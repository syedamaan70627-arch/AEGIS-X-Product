import assert from "node:assert";
import { test } from "node:test";
import { setAuthToken } from "../lib/api";
import { getStoredAuthToken, setStoredAuthToken } from "../lib/auth";

test("Auth Infrastructure: Token storage and injection", () => {
  setStoredAuthToken("mock-jwt-token-12345");
  const stored = getStoredAuthToken();
  assert.strictEqual(stored, "mock-jwt-token-12345");

  setAuthToken("mock-jwt-token-67890");
  assert.strictEqual(getStoredAuthToken(), "mock-jwt-token-67890");

  setStoredAuthToken(null);
  assert.strictEqual(getStoredAuthToken(), null);
});

test("Auth Infrastructure: Service role key is not exposed", () => {
  assert.strictEqual(process.env.SUPABASE_SERVICE_ROLE_KEY, undefined);
});
