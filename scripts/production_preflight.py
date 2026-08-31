"""
AEGIS-X Production Preflight & Import Safety Guard.

Automatically verifies:
1. Static analysis for undefined typing names (Optional, Tuple, Any, etc.)
2. Bytecode compilation across all production modules
3. Programmatic import of every module under api/ and aegis/
4. FastAPI application import (from api.main import app)
5. Production HTTP uvicorn startup & /health endpoint responsiveness
"""

import ast
import glob
import importlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def run_static_typing_check() -> bool:
    print("--- 1. Running Static Typing & Undefined Name Check ---")
    typing_names = {
        'Optional', 'Any', 'List', 'Dict', 'Tuple', 'Union', 'Path',
        'Literal', 'Callable', 'Sequence', 'Mapping', 'Set'
    }

    all_files = (
        glob.glob(str(BASE_DIR / "api" / "**" / "*.py"), recursive=True) +
        glob.glob(str(BASE_DIR / "aegis" / "**" / "*.py"), recursive=True)
    )

    issues = 0
    for fpath in sorted(all_files):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=fpath)
        except Exception as e:
            print(f"FAILED: Syntax error in {fpath}: {e}")
            issues += 1
            continue

        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in typing_names:
                if node.id not in imported_names:
                    rel_path = Path(fpath).relative_to(BASE_DIR)
                    print(f"FAILED: {rel_path}:{node.lineno} -> Undefined typing symbol '{node.id}'")
                    issues += 1

    if issues == 0:
        print("  Static Typing Check: PASSED (0 undefined typing names)")
        return True
    return False


def run_compileall_check() -> bool:
    print("--- 2. Running Python Bytecode Compile Check ---")
    import compileall
    api_dir = str(BASE_DIR / "api")
    aegis_dir = str(BASE_DIR / "aegis")

    res_api = compileall.compile_dir(api_dir, quiet=1)
    res_aegis = compileall.compile_dir(aegis_dir, quiet=1)

    if res_api and res_aegis:
        print("  Python Compile Check: PASSED")
        return True
    print("FAILED: Compileall found errors.")
    return False


def run_full_module_import_audit() -> bool:
    print("--- 3. Running Programmatic Module Import Audit ---")
    api_files = glob.glob(str(BASE_DIR / "api" / "**" / "*.py"), recursive=True)
    aegis_files = glob.glob(str(BASE_DIR / "aegis" / "**" / "*.py"), recursive=True)

    failed_modules = []
    for fpath in sorted(api_files + aegis_files):
        rel = Path(fpath).relative_to(BASE_DIR)
        mod_parts = list(rel.with_suffix("").parts)
        if mod_parts[-1] == "__init__":
            mod_parts = mod_parts[:-1]
        if not mod_parts:
            continue
        mod_name = ".".join(mod_parts)

        try:
            importlib.import_module(mod_name)
        except Exception as e:
            print(f"FAILED: Could not import '{mod_name}': {e}")
            failed_modules.append((mod_name, str(e)))

    if not failed_modules:
        print("  Module Import Audit: PASSED (All production modules imported cleanly)")
        return True
    return False


def run_fastapi_app_check() -> bool:
    print("--- 4. Running FastAPI App Import Check ---")
    try:
        from api.main import app
        print(f"  FastAPI App Check: PASSED (App title: '{app.title}')")
        return True
    except Exception as e:
        print(f"FAILED: Could not import api.main:app: {e}")
        return False


def run_production_server_smoke_test() -> bool:
    print("--- 5. Running Production Server HTTP /health Smoke Test ---")
    import subprocess

    port = 8008
    cmd = [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(2.5)

    try:
        url = f"http://127.0.0.1:{port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if resp.status == 200 and body.get("status") == "ok":
                print(f"  HTTP Health Check: PASSED (200 OK: {body})")
                proc.terminate()
                proc.wait(timeout=3)
                return True
    except Exception as e:
        print(f"FAILED: Health check failed: {e}")
    finally:
        if proc.poll() is None:
            proc.kill()

    return False


def main():
    print("=================================================================")
    print("            AEGIS-X PRODUCTION PREFLIGHT GUARD VERIFICATION      ")
    print("=================================================================")

    ok1 = run_static_typing_check()
    ok2 = run_compileall_check()
    ok3 = run_full_module_import_audit()
    ok4 = run_fastapi_app_check()
    ok5 = run_production_server_smoke_test()

    if all([ok1, ok2, ok3, ok4, ok5]):
        print("\n=================================================================")
        print("     PRODUCTION PREFLIGHT PASSED PERFECTLY: READY TO DEPLOY      ")
        print("=================================================================")
        sys.exit(0)
    else:
        print("\n=================================================================")
        print("     PRODUCTION PREFLIGHT FAILED: DO NOT DEPLOY                  ")
        print("=================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
