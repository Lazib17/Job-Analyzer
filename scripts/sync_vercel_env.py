"""Upload selected backend env vars to Vercel without printing secret values."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"

KEYS = (
    "SECRET_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "SUPABASE_SERVICE_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_MODEL",
)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def add_env(name: str, value: str, target: str) -> bool:
    result = subprocess.run(
        ["npx", "vercel", "env", "add", name, target],
        input=value + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        shell=True,
    )
    ok = result.returncode == 0 or "already exists" in (result.stderr + result.stdout).lower()
    print(f"{name} -> {target}: {'ok' if ok else 'failed'}")
    if not ok:
        err = result.stderr.strip() or result.stdout.strip()
        print(err[:300])
    return ok


def main() -> int:
    if not ENV_PATH.exists():
        print("backend/.env not found")
        return 1
    values = load_env(ENV_PATH)
    values["CORS_ORIGINS"] = (
        "http://localhost:5173,http://localhost:3000,"
        "https://job-analyzer-eight.vercel.app"
    )
    failed = False
    for key in KEYS + ("CORS_ORIGINS",):
        value = values.get(key, "")
        if not value:
            print(f"{key}: skipped (empty)")
            continue
        for target in ("production", "preview"):
            if not add_env(key, value, target):
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
