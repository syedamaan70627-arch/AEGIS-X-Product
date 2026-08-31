const AUTH_TOKEN_KEY = "aegisx_auth_token";
let inMemoryToken: string | null = null;

export const getStoredAuthToken = (): string | null => {
  if (typeof window !== "undefined" && window.localStorage) {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }
  return inMemoryToken;
};

export const setStoredAuthToken = (token: string | null): void => {
  inMemoryToken = token;
  if (typeof window !== "undefined" && window.localStorage) {
    if (token) {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  }
};
