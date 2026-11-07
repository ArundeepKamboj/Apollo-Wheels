"""Start all local services with one command; Ctrl+C stops the full stack."""

from __future__ import annotations

import os
import argparse
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all local APIs and the frontend, or one service.")
    parser.add_argument("--only", choices=["contract", "pricing", "billing", "frontend"],
                        help="Run a single service for local development.")
    parser.add_argument("--config", help="Use a specific environment file instead of config/local.env.")
    args = parser.parse_args()
    config = (ROOT / args.config) if args.config else ROOT / "config" / "local.env"
    if not args.config and not config.exists():
        config = ROOT / "config" / "local.env.example"
    settings = load_env(config)
    env = os.environ.copy()
    env.update(settings)
    env["APOLLO_DB_PATH"] = str((ROOT / settings.get("APOLLO_DB_PATH", "data/apollo_wheels.db")).resolve())
    env["APOLLO_DOCUMENT_DIR"] = str((ROOT / settings.get("APOLLO_DOCUMENT_DIR", "data/documents")).resolve())
    env["CONTRACT_API_URL"] = settings.get("CONTRACT_API_URL", "http://127.0.0.1:8001")
    env["PRICING_API_URL"] = settings.get("PRICING_API_URL", "http://127.0.0.1:8002")
    env["BILLING_API_URL"] = settings.get("BILLING_API_URL", "http://127.0.0.1:8003")
    env["AUTH_API_URL"] = settings.get("AUTH_API_URL", "http://127.0.0.1:8004")
    env["API_GATEWAY_URL"] = settings.get("API_GATEWAY_URL", "http://127.0.0.1:8000")
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "src"), env.get("PYTHONPATH", "")])

    runtime = ROOT / "frontend" / "runtime-config.js"
    runtime.write_text(
        f"window.APOLLO_CONFIG = {{gatewayApi:{env['API_GATEWAY_URL']!r}}};\n",
        encoding="utf-8",
    )

    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    host = env.get("HOST", "127.0.0.1")
    commands = [
        ("auth", [sys.executable, "-m", "uvicorn", "services.auth_service.main:app", "--host",
                   host, "--port", env.get("AUTH_API_PORT", "8004")],
         f"{env['AUTH_API_URL']}/"),
        ("contract", [sys.executable, "-m", "uvicorn", "services.contract_service.main:app", "--host",
                       host, "--port", env.get("CONTRACT_API_PORT", "8001")],
         f"http://{host}:{env.get('CONTRACT_API_PORT','8001')}/"),
        ("pricing", [sys.executable, "-m", "uvicorn", "services.pricing_service.main:app", "--host",
                     host, "--port", env.get("PRICING_API_PORT", "8002")],
         f"http://{host}:{env.get('PRICING_API_PORT','8002')}/"),
        ("billing", [sys.executable, "-m", "uvicorn", "services.billing_service.main:app", "--host",
                     host, "--port", env.get("BILLING_API_PORT", "8003")],
         f"http://{host}:{env.get('BILLING_API_PORT','8003')}/"),
        ("gateway", [sys.executable, "-m", "uvicorn", "services.api_gateway.main:app", "--host",
                     host, "--port", env.get("API_GATEWAY_PORT", "8000")],
         f"{env['API_GATEWAY_URL']}/health"),
        ("frontend", [sys.executable, "-m", "http.server", env.get("FRONTEND_PORT", "5173"), "--bind",
                       host, "--directory", str(ROOT / "frontend")],
         f"http://{host}:{env.get('FRONTEND_PORT','5173')}/"),
    ]
    if args.only:
        commands = [entry for entry in commands if entry[0] == args.only]
    processes: list[tuple[str, subprocess.Popen]] = []
    handles = []
    try:
        for name, command, health_url in commands:
            handle = (logs / f"{name}.log").open("a", encoding="utf-8")
            handles.append(handle)
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            processes.append((name, process))
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError(f"{name} exited during startup. Check logs/{name}.log")
                try:
                    with urlopen(health_url, timeout=1):
                        break
                except (URLError, TimeoutError, OSError):
                    time.sleep(0.2)
            else:
                raise RuntimeError(f"{name} did not become ready. Check logs/{name}.log")
        print("Apollo Wheels local MVP is running")
        print(f"Frontend:     http://{host}:{env.get('FRONTEND_PORT','5173')}")
        print(f"API Gateway:  {env['API_GATEWAY_URL']}")
        print(f"Gateway docs: {env['API_GATEWAY_URL']}/docs")
        print(f"Auth API:     {env['AUTH_API_URL']}/docs")
        print(f"Contract API: {env['CONTRACT_API_URL']}/docs")
        print(f"Pricing API:  {env['PRICING_API_URL']}/docs")
        print(f"Billing API:  {env['BILLING_API_URL']}/docs")
        print("Press Ctrl+C to stop all services. Service logs are in ./logs.")
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    raise RuntimeError(f"{name} stopped. Check logs/{name}.log")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping local services...")
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        for _, process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for _, process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        for handle in handles:
            handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
