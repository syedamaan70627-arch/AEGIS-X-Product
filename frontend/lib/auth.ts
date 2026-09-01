let inMemoryToken: string | null = null;

export const getStoredAuthToken = (): string | null => {
  return inMemoryToken;
};

export const setStoredAuthToken = (token: string | null): void => {
  inMemoryToken = token;
  if (typeof window !== "undefined" && window.localStorage) {
    // Clear legacy aegisx_auth_token so stale custom localStorage tokens never override Supabase session
    window.localStorage.removeItem("aegisx_auth_token");
  }
};

