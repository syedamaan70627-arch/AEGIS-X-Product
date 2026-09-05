/**
 * AEGIS-X Centralized Authentication Error Classification
 */

export interface AuthErrorDetails {
  code: string;
  title: string;
  message: string;
  isUnconfirmedEmail: boolean;
  isRateLimited: boolean;
}

export function maskEmail(email: string): string {
  if (!email || !email.includes("@")) return email || "";
  const [local, domain] = email.split("@");
  if (local.length <= 1) {
    return `${local}***@${domain}`;
  }
  if (local.length === 2) {
    return `${local[0]}*@${domain}`;
  }
  return `${local[0]}***${local[local.length - 1]}@${domain}`;
}

export function classifyAuthError(err: any): AuthErrorDetails {
  if (!err) {
    return {
      code: "unexpected_failure",
      title: "Authentication Error",
      message: "An unexpected authentication error occurred. Please try again.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  const rawCode = (err.code || err.error_code || err.status || "").toString().toLowerCase();
  const rawMsg = (err.message || err.error_description || (typeof err === "string" ? err : "")).toString();
  const lowerMsg = rawMsg.toLowerCase();

  // 1. Email not confirmed
  if (
    rawCode === "email_not_confirmed" ||
    lowerMsg.includes("email not confirmed") ||
    lowerMsg.includes("email_not_confirmed") ||
    lowerMsg.includes("unconfirmed email")
  ) {
    return {
      code: "email_not_confirmed",
      title: "Email Verification Required",
      message: "Please verify your email address before signing in. Check your inbox or request a new verification email.",
      isUnconfirmedEmail: true,
      isRateLimited: false,
    };
  }

  // 2. Over rate limit
  if (
    rawCode === "over_email_send_rate_limit" ||
    rawCode === "rate_limit_exceeded" ||
    rawCode === "429" ||
    lowerMsg.includes("rate limit") ||
    lowerMsg.includes("too many requests") ||
    lowerMsg.includes("email_rate_limit")
  ) {
    return {
      code: "over_email_send_rate_limit",
      title: "Rate Limit Exceeded",
      message: "Too many verification attempts. Please wait a minute before requesting another email.",
      isUnconfirmedEmail: false,
      isRateLimited: true,
    };
  }

  // 3. Invalid credentials
  if (
    rawCode === "invalid_credentials" ||
    rawCode === "invalid_grant" ||
    lowerMsg.includes("invalid login credentials") ||
    lowerMsg.includes("invalid credentials") ||
    lowerMsg.includes("user not found")
  ) {
    return {
      code: "invalid_credentials",
      title: "Invalid Credentials",
      message: "Invalid email or password. Please verify your login credentials and try again.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  // 4. Invalid or expired token / link
  if (
    rawCode === "otp_expired" ||
    rawCode === "token_expired" ||
    lowerMsg.includes("token is expired") ||
    lowerMsg.includes("token has expired") ||
    lowerMsg.includes("invalid token") ||
    lowerMsg.includes("otp expired")
  ) {
    return {
      code: "otp_expired",
      title: "Verification Link Invalid or Expired",
      message: "The verification link is invalid or has expired. Request a new verification email to continue.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  // 5. Weak password
  if (rawCode === "weak_password" || lowerMsg.includes("password should be at least")) {
    return {
      code: "weak_password",
      title: "Password Requirements Unmet",
      message: "Password should be at least 8 characters long and meet complexity requirements.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  // 6. Email address invalid
  if (rawCode === "email_address_invalid" || lowerMsg.includes("invalid email")) {
    return {
      code: "email_address_invalid",
      title: "Invalid Email Address",
      message: "Please enter a valid work email address.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  // 7. Signup disabled
  if (rawCode === "signup_disabled" || lowerMsg.includes("signup disabled")) {
    return {
      code: "signup_disabled",
      title: "Registration Unavailable",
      message: "New user signups are currently restricted by administrator policy.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  // 8. Network unavailable
  if (lowerMsg.includes("failed to fetch") || lowerMsg.includes("networkerror")) {
    return {
      code: "network_error",
      title: "Network Error",
      message: "Unable to connect to authentication server. Please check your internet connection.",
      isUnconfirmedEmail: false,
      isRateLimited: false,
    };
  }

  // Fallback: Generic, safe error message (no internal provider or backend crashes exposed)
  return {
    code: "unexpected_failure",
    title: "Authentication Failed",
    message: rawMsg && !rawMsg.includes("AuthApiError") && !rawMsg.includes("{") ? rawMsg : "An error occurred during authentication. Please try again.",
    isUnconfirmedEmail: false,
    isRateLimited: false,
  };
}
