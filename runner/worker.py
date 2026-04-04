#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONTROL_SERVER = PROJECT_ROOT / "scripts" / "gh_control_server.py"


def http_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def poll_next_job(api_base: str) -> dict[str, Any] | None:
    payload = http_json("GET", f"{api_base}/api/queue/next")
    return payload.get("job")


def claim_job(api_base: str, job_id: str) -> dict[str, Any]:
    payload = http_json("POST", f"{api_base}/api/jobs/{job_id}/claim", {})
    return payload["job"]


def complete_job(api_base: str, job_id: str, result: dict[str, Any]) -> None:
    http_json("POST", f"{api_base}/api/jobs/{job_id}/complete", {"result": result})


def fail_job(api_base: str, job_id: str, error: str) -> None:
    http_json("POST", f"{api_base}/api/jobs/{job_id}/fail", {"error": error})


def apply_job_locally(job: dict[str, Any], local_api_base: str) -> dict[str, Any]:
    """Proxy a queued deploy job into the current local Rhino control server.

    This keeps the deployment scaffold compatible with the working local prototype.
    Once the runner is fully productionized, this function can be replaced with a
    direct RhinoMCP integration that does not depend on the local HTTP bridge.
    """

    return http_json(
        "POST",
        f"{local_api_base}/api/controls",
        {"id": job["control_id"], "value": job["value"]},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Poll deploy API and execute Rhino jobs locally.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8787")
    parser.add_argument("--local-api-base", default="http://127.0.0.1:8001")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(f"Runner polling {args.api_base} and forwarding jobs to {args.local_api_base}")

    while True:
        try:
            job = poll_next_job(args.api_base)
            if not job:
                if args.once:
                    return 0
                time.sleep(args.interval)
                continue

            claimed = claim_job(args.api_base, job["id"])
            result = apply_job_locally(claimed, args.local_api_base)
            if not result.get("ok"):
                raise RuntimeError(result.get("error", "Local control update failed."))
            complete_job(args.api_base, claimed["id"], result)
        except urllib.error.URLError as error:
            print(f"[runner] network error: {error}")
        except Exception as error:
            if "claimed" in locals():
                try:
                    fail_job(args.api_base, claimed["id"], str(error))
                except Exception as nested:
                    print(f"[runner] failed to mark job as failed: {nested}")
            print(f"[runner] error: {error}")
        finally:
            if args.once:
                return 0
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
