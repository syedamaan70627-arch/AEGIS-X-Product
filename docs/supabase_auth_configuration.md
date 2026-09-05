# AEGIS-X Supabase Auth Configuration Audit & Setup Guide

**Target Supabase Project ID**: `kiczqwyuzjjvlmjpuuuv`

---

## 1. Authentication -> URL Configuration

Navigate to **Authentication -> URL Configuration** in the Supabase Dashboard:

### Site URL
```
https://aegis-x-product.vercel.app
```

### Redirect URLs
Add only the required exact production and local callback endpoints:

```
https://aegis-x-product.vercel.app/auth/confirm
https://aegis-x-product.vercel.app/auth/callback
http://localhost:3000/auth/confirm
http://localhost:3000/auth/callback
http://127.0.0.1:3000/auth/confirm
```

> [!IMPORTANT]
> Do not add unnecessary broad wildcards (such as `https://*` or `*`). Restrict redirect URLs to explicit endpoints to enforce open-redirect security invariants.

---

## 2. Authentication -> Email Templates -> Confirm signup

Navigate to **Authentication -> Email Templates -> Confirm signup**:

### Subject
```
Confirm your AEGIS-X account
```

### Body (HTML)
Copy and paste the full HTML contents from [confirm_signup.html](file:///c:/Users/2403a/Documents/AEGIS-X-Product/docs/email_templates/confirm_signup.html):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Confirm Your AEGIS-X Account</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0B0F14; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #F3F4F6;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0B0F14; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #151B23; border: 1px solid #26303D; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
          
          <tr>
            <td align="center" style="padding-bottom: 24px;">
              <div style="display: inline-block; width: 48px; height: 48px; background-color: #3B82F6; border-radius: 12px; line-height: 48px; text-align: center; color: #ffffff; font-weight: bold; font-size: 20px; margin-bottom: 12px;">
                🛡️
              </div>
              <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #F3F4F6;">AEGIS-X</h1>
              <p style="margin: 4px 0 0 0; font-size: 12px; color: #9CA3AF;">Reliability Telemetry &amp; AI Early Warning</p>
            </td>
          </tr>

          <tr>
            <td style="border-top: 1px solid #26303D; padding-top: 24px;"></td>
          </tr>

          <tr>
            <td style="padding-bottom: 24px;">
              <h2 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #F3F4F6;">Confirm Your Email Address</h2>
              <p style="margin: 0 0 16px 0; font-size: 13px; line-height: 1.6; color: #9CA3AF;">
                Thank you for creating an account with AEGIS-X. Please confirm your email address to complete registration and access the reliability command center.
              </p>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding-bottom: 28px;">
              <a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=signup&next=/dashboard" target="_blank" style="display: inline-block; background-color: #3B82F6; color: #ffffff; font-size: 13px; font-weight: 600; text-decoration: none; padding: 12px 28px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">
                Confirm Email Address
              </a>
            </td>
          </tr>

          <tr>
            <td style="background-color: #0F141B; border: 1px solid #26303D; border-radius: 10px; padding: 16px; margin-bottom: 24px;">
              <p style="margin: 0 0 8px 0; font-size: 11px; font-weight: 600; color: #F3F4F6; text-transform: uppercase; letter-spacing: 0.05em;">Security Notice &amp; Guidance</p>
              <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #9CA3AF; line-height: 1.5;">
                <li>This verification link is valid for single use only.</li>
                <li>If the button does not work, copy and paste the plain link below into your web browser.</li>
                <li>If you did not create an AEGIS-X account, you can safely ignore this email.</li>
              </ul>
            </td>
          </tr>

          <tr>
            <td style="padding-top: 16px; padding-bottom: 24px;">
              <p style="margin: 0 0 6px 0; font-size: 11px; color: #6B7280;">Direct Verification Link:</p>
              <p style="margin: 0; font-size: 11px; font-family: monospace; color: #3B82F6; word-break: break-all; line-height: 1.4;">
                {{ .ConfirmationURL }}
              </p>
            </td>
          </tr>

          <tr>
            <td style="border-top: 1px solid #26303D; padding-top: 20px; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #6B7280;">
                © 2026 AEGIS-X Framework. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

---

## 3. Verification Steps
1. Save changes in Supabase Dashboard.
2. Sign up a new user via `https://aegis-x-product.vercel.app/signup`.
3. Check recipient inbox -> verify email layout, logo, button destination (`/auth/confirm`), and direct fallback URL.
