/**
 * AEGIS-X Vercel Deployment Configuration Unit Tests
 */

import test from "node:test";
import assert from "node:assert/strict";
import { getEnvConfig, isPlaceholderUrl, isPlaceholderKey, isVercelEnvironment } from "../lib/config";
import { getApiBaseUrl, getApiServerRoot } from "../lib/api";

test("Vercel Config: Environment Detection & Placeholder Identifiers", () => {
  assert.equal(isPlaceholderUrl("http://localhost:8000/api/v1"), true);
  assert.equal(isPlaceholderUrl("http://127.0.0.1:8000/api/v1"), true);
  assert.equal(isPlaceholderUrl("https://placeholder-project.supabase.co"), true);
  assert.equal(isPlaceholderUrl("https://aegis-x-product-production.up.railway.app/api/v1"), false);

  assert.equal(isPlaceholderKey("placeholder-anon-key"), true);
  assert.equal(isPlaceholderKey("your-anon-key"), true);
  assert.equal(isPlaceholderKey("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validkey"), false);
});

test("Vercel Config: Missing NEXT_PUBLIC_API_BASE_URL Fails Validation on Vercel", () => {
  const oldVercel = process.env.NEXT_PUBLIC_VERCEL_ENV;
  const oldApi = process.env.NEXT_PUBLIC_API_BASE_URL;

  try {
    process.env.NEXT_PUBLIC_VERCEL_ENV = "preview";
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    const cfg = getEnvConfig();
    assert.equal(cfg.isVercel, true);
    assert.equal(cfg.isValid, false);
    assert.equal(cfg.missingVars.includes("NEXT_PUBLIC_API_BASE_URL"), true);
    assert.equal(cfg.apiBaseUrl, "");
  } finally {
    if (oldVercel) process.env.NEXT_PUBLIC_VERCEL_ENV = oldVercel;
    else delete process.env.NEXT_PUBLIC_VERCEL_ENV;

    if (oldApi) process.env.NEXT_PUBLIC_API_BASE_URL = oldApi;
    else delete process.env.NEXT_PUBLIC_API_BASE_URL;
  }
});

test("Vercel Config: Missing NEXT_PUBLIC_SUPABASE_URL Fails Validation on Vercel", () => {
  const oldVercel = process.env.NEXT_PUBLIC_VERCEL_ENV;
  const oldSupa = process.env.NEXT_PUBLIC_SUPABASE_URL;

  try {
    process.env.NEXT_PUBLIC_VERCEL_ENV = "production";
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;

    const cfg = getEnvConfig();
    assert.equal(cfg.isVercel, true);
    assert.equal(cfg.isValid, false);
    assert.equal(cfg.missingVars.includes("NEXT_PUBLIC_SUPABASE_URL"), true);
  } finally {
    if (oldVercel) process.env.NEXT_PUBLIC_VERCEL_ENV = oldVercel;
    else delete process.env.NEXT_PUBLIC_VERCEL_ENV;

    if (oldSupa) process.env.NEXT_PUBLIC_SUPABASE_URL = oldSupa;
    else delete process.env.NEXT_PUBLIC_SUPABASE_URL;
  }
});

test("Vercel Config: Missing NEXT_PUBLIC_SUPABASE_ANON_KEY Fails Validation on Vercel", () => {
  const oldVercel = process.env.NEXT_PUBLIC_VERCEL_ENV;
  const oldKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  try {
    process.env.NEXT_PUBLIC_VERCEL_ENV = "preview";
    delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    const cfg = getEnvConfig();
    assert.equal(cfg.isVercel, true);
    assert.equal(cfg.isValid, false);
    assert.equal(cfg.missingVars.includes("NEXT_PUBLIC_SUPABASE_ANON_KEY"), true);
  } finally {
    if (oldVercel) process.env.NEXT_PUBLIC_VERCEL_ENV = oldVercel;
    else delete process.env.NEXT_PUBLIC_VERCEL_ENV;

    if (oldKey) process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = oldKey;
    else delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  }
});

test("Vercel Config: Local Dev Fallbacks Allowed ONLY outside Vercel", () => {
  const oldVercel = process.env.NEXT_PUBLIC_VERCEL_ENV;
  const oldVercelUrl = process.env.NEXT_PUBLIC_VERCEL_URL;
  const oldVercel1 = process.env.VERCEL;
  const oldApi = process.env.NEXT_PUBLIC_API_BASE_URL;

  try {
    delete process.env.NEXT_PUBLIC_VERCEL_ENV;
    delete process.env.NEXT_PUBLIC_VERCEL_URL;
    delete process.env.VERCEL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    const cfg = getEnvConfig();
    assert.equal(cfg.isVercel, false);
    assert.equal(cfg.isValid, true);
    assert.equal(cfg.apiBaseUrl, "http://127.0.0.1:8000/api/v1");
  } finally {
    if (oldVercel) process.env.NEXT_PUBLIC_VERCEL_ENV = oldVercel;
    if (oldVercelUrl) process.env.NEXT_PUBLIC_VERCEL_URL = oldVercelUrl;
    if (oldVercel1) process.env.VERCEL = oldVercel1;
    if (oldApi) process.env.NEXT_PUBLIC_API_BASE_URL = oldApi;
  }
});

test("Vercel Config: Server Root Resolution for Railway Backend", () => {
  const oldApi = process.env.NEXT_PUBLIC_API_BASE_URL;
  const oldVercel = process.env.NEXT_PUBLIC_VERCEL_ENV;

  try {
    process.env.NEXT_PUBLIC_VERCEL_ENV = "production";
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://aegis-x-product-production.up.railway.app/api/v1";

    const root = getApiServerRoot();
    assert.equal(root, "https://aegis-x-product-production.up.railway.app");
  } finally {
    if (oldApi) process.env.NEXT_PUBLIC_API_BASE_URL = oldApi;
    else delete process.env.NEXT_PUBLIC_API_BASE_URL;

    if (oldVercel) process.env.NEXT_PUBLIC_VERCEL_ENV = oldVercel;
    else delete process.env.NEXT_PUBLIC_VERCEL_ENV;
  }
});
