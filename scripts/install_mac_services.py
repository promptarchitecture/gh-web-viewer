#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
LOGS_DIR = Path.home() / "Library" / "Logs" / "gh-web-viewer"
CONTROL_LABEL = "com.promptarchitecture.gh-web-viewer.control-server"
WORKER_LABEL = "com.promptarchitecture.gh-web-viewer.worker"
DEFAULT_PUBLIC_API_BASE = "https://gh-web-viewer-api.onrender.com"
DEFAULT_LOCAL_API_BASE = "http://127.0.0.1:8001"


def plist_path(label: str) -> Path:
    return LAUNCH_AGENTS_DIR / f"{label}.plist"


def build_control_plist(python_executable: str) -> dict[str, object]:
    script_path = PROJECT_ROOT / "scripts" / "gh_control_server.py"
    return {
        "Label": CONTROL_LABEL,
        "ProgramArguments": [python_executable, str(script_path)],
        "WorkingDirectory": str(PROJECT_ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOGS_DIR / "gh_control_server.stdout.log"),
        "StandardErrorPath": str(LOGS_DIR / "gh_control_server.stderr.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
        },
    }


def build_worker_plist(
    python_executable: str,
    public_api_base: str,
    local_api_base: str,
    insecure: bool,
) -> dict[str, object]:
    script_path = PROJECT_ROOT / "runner" / "worker.py"
    program_arguments = [
        python_executable,
        str(script_path),
        "--api-base",
        public_api_base,
        "--local-api-base",
        local_api_base,
    ]
    if insecure:
        program_arguments.append("--insecure")

    return {
        "Label": WORKER_LABEL,
        "ProgramArguments": program_arguments,
        "WorkingDirectory": str(PROJECT_ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOGS_DIR / "worker.stdout.log"),
        "StandardErrorPath": str(LOGS_DIR / "worker.stderr.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
        },
    }


def write_plist(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump(payload, handle, sort_keys=False)


def launchctl_bootout(label: str) -> None:
    domain = f"gui/{os.getuid()}"
    subprocess.run(
        ["launchctl", "bootout", domain, str(plist_path(label))],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def launchctl_bootstrap(label: str) -> None:
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootstrap", domain, str(plist_path(label))], check=True)
    subprocess.run(["launchctl", "enable", f"{domain}/{label}"], check=False)
    subprocess.run(["launchctl", "kickstart", "-k", f"{domain}/{label}"], check=False)


def install_agents(public_api_base: str, local_api_base: str, insecure: bool) -> None:
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    python_executable = sys.executable
    write_plist(plist_path(CONTROL_LABEL), build_control_plist(python_executable))
    write_plist(
        plist_path(WORKER_LABEL),
        build_worker_plist(python_executable, public_api_base, local_api_base, insecure),
    )

    for label in (CONTROL_LABEL, WORKER_LABEL):
        launchctl_bootout(label)
        launchctl_bootstrap(label)


def uninstall_agents() -> None:
    for label in (CONTROL_LABEL, WORKER_LABEL):
        launchctl_bootout(label)
        path = plist_path(label)
        if path.exists():
            path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install gh-web-viewer macOS LaunchAgents.")
    parser.add_argument("--public-api-base", default=DEFAULT_PUBLIC_API_BASE)
    parser.add_argument("--local-api-base", default=DEFAULT_LOCAL_API_BASE)
    parser.add_argument(
        "--no-insecure-worker",
        action="store_true",
        help="Do not pass --insecure to the worker launch agent.",
    )
    parser.add_argument("--uninstall", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.uninstall:
        uninstall_agents()
        print("Removed gh-web-viewer launch agents.")
        return 0

    install_agents(
        public_api_base=args.public_api_base,
        local_api_base=args.local_api_base,
        insecure=not args.no_insecure_worker,
    )
    print("Installed and started gh-web-viewer launch agents.")
    print(f"- control: {plist_path(CONTROL_LABEL)}")
    print(f"- worker:  {plist_path(WORKER_LABEL)}")
    print(f"- logs:    {LOGS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
