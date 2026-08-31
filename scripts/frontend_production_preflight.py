"""
AEGIS-X Frontend Production Preflight & Vercel Deployment Guard.

Automatically verifies:
1. Frontend package & App Router structure
2. Required routes existence (/ , /login, /signup, /dashboard, /settings)
3. Absence of backend secrets in frontend source and environment files
4. Production build execution (npm run build in frontend/)
5. Production HTTP route serving (/ , /login, /signup, /dashboard, /settings)
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def check_frontend_structure() -> bool:
    print("--- 1. Checking Frontend Package & App Router Structure ---")
    pkg_path = FRONTEND_DIR / "package.json"
    if not pkg_path.exists():
        print("FAILED: frontend/package.json does not exist.")
        return False

    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    if "next" not in deps:
        print("FAILED: 'next' dependency missing from frontend/package.json.")
        return False

    app_dir = FRONTEND_DIR / "app"
    if not app_dir.exists():
        print("FAILED: frontend/app directory does not exist.")
        return False

    required_routes = ["page.tsx", "login/page.tsx", "signup/page.tsx", "dashboard/page.tsx", "settings/page.tsx"]
    for route in required_routes:
        rpath = app_dir / route
        if not rpath.exists():
            print(f"FAILED: Required route frontend/app/{route} missing.")
            return False

    print("  Structure Check: PASSED")
    return True


def check_secret_exposure() -> bool:
    print("--- 2. Auditing Secret Exposure in Frontend ---")
    forbidden_patterns = ["SUPABASE_SERVICE_ROLE_KEY", "sb_secret", "SERVICE_ROLE"]
    exposed = []

    # Check source files in frontend/ (excluding tests) and frontend/.env.local if present
    for root, _, files in os.walk(FRONTEND_DIR):
        if "node_modules" in root or ".next" in root or "__tests__" in root:
            continue
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx", ".json", ".env.local", ".env.example")):
                fpath = Path(root) / file
                try:
                    content = fpath.read_text(encoding="utf-8")
                    for pattern in forbidden_patterns:
                        if pattern in content:
                            exposed.append((fpath.relative_to(BASE_DIR), pattern))
                except Exception:
                    pass

    if exposed:
        for fpath, pat in exposed:
            print(f"FAILED: Forbidden secret pattern '{pat}' found in {fpath}")
        return False

    print("  Secret Audit: PASSED (0 backend secrets in frontend)")
    return True


def check_production_build() -> bool:
    print("--- 3. Running Next.js Production Build (npm run build) ---")
    res = subprocess.run(["npm", "run", "build"], cwd=str(FRONTEND_DIR), capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        print(f"FAILED: Next.js production build failed:\n{res.stderr}")
        return False

    print("  Production Build: PASSED")
    return True


def check_http_route_serving() -> bool:
    print("--- 4. Running Production HTTP Route Serving Test ---")
    port = 3009
    env = {**os.environ, "PORT": str(port)}
    cmd = "npm run start"
    proc = subprocess.Popen(cmd, cwd=str(FRONTEND_DIR), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    time.sleep(4.0)

    routes_to_test = [
        ("/", [200, 307, 308]),
        ("/login", [200]),
        ("/signup", [200]),
        ("/dashboard", [200]),
        ("/settings", [200]),
    ]

    all_passed = True
    for route, expected_codes in routes_to_test:
        url = f"http://127.0.0.1:{port}{route}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AEGIS-X-Preflight"})
            # Custom HTTPRedirectHandler to catch 307/308 redirects
            class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None

            opener = urllib.request.build_opener(NoRedirectHandler())
            try:
                resp = opener.open(req, timeout=5)
                status_code = resp.status
            except urllib.error.HTTPError as he:
                status_code = he.code

            if status_code in expected_codes:
                print(f"  Route '{route}' -> HTTP {status_code} (PASSED)")
            else:
                print(f"FAILED: Route '{route}' returned HTTP {status_code}, expected {expected_codes}")
                all_passed = False
        except Exception as e:
            print(f"FAILED: Could not fetch route '{route}': {e}")
            all_passed = False

    if proc.poll() is None:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)

    return all_passed


def main():
    print("=================================================================")
    print("        AEGIS-X FRONTEND PRODUCTION PREFLIGHT VERIFICATION       ")
    print("=================================================================")

    ok1 = check_frontend_structure()
    ok2 = check_secret_exposure()
    ok3 = check_production_build()
    ok4 = check_http_route_serving()

    if all([ok1, ok2, ok3, ok4]):
        print("\n=================================================================")
        print("  FRONTEND PREFLIGHT PASSED PERFECTLY: VERCEL DEPLOYMENT READY   ")
        print("=================================================================")
        sys.exit(0)
    else:
        print("\n=================================================================")
        print("  FRONTEND PREFLIGHT FAILED: DO NOT DEPLOY TO VERCEL             ")
        print("=================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
