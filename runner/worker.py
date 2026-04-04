#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONTROL_SERVER = PROJECT_ROOT / "scripts" / "gh_control_server.py"
OUTPUT_DIR = PROJECT_ROOT / "output" / "latest"
LOCAL_CONTROLS_PATH = OUTPUT_DIR / "controls.json"
LOCAL_SUMMARY_PATH = OUTPUT_DIR / "summary.json"
LOCAL_MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
LOCAL_MODEL_PATH = OUTPUT_DIR / "current-preview.3dm"


def url_uses_https(url: str) -> bool:
    return url.lower().startswith("https://")


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    insecure: bool = False,
) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    context = None
    if url_uses_https(url):
        context = ssl._create_unverified_context() if insecure else ssl.create_default_context()

    with urllib.request.urlopen(request, timeout=20, context=context) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def poll_next_job(api_base: str, *, insecure: bool) -> dict[str, Any] | None:
    payload = http_json("GET", f"{api_base}/api/queue/next", insecure=insecure)
    return payload.get("job")


def claim_job(api_base: str, job_id: str, *, insecure: bool) -> dict[str, Any]:
    payload = http_json("POST", f"{api_base}/api/jobs/{job_id}/claim", {}, insecure=insecure)
    return payload["job"]


def complete_job(api_base: str, job_id: str, result: dict[str, Any], *, insecure: bool) -> None:
    http_json(
        "POST",
        f"{api_base}/api/jobs/{job_id}/complete",
        {"result": result},
        insecure=insecure,
    )


def fail_job(api_base: str, job_id: str, error: str, *, insecure: bool) -> None:
    http_json("POST", f"{api_base}/api/jobs/{job_id}/fail", {"error": error}, insecure=insecure)


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


def load_local_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def sync_published_outputs(api_base: str, *, insecure: bool) -> dict[str, Any]:
    controls = load_local_json(LOCAL_CONTROLS_PATH, {"title": "웹 제어 입력", "items": []})
    summary = load_local_json(LOCAL_SUMMARY_PATH, {"title": "SUMMARY", "sections": []})
    manifest = load_local_json(LOCAL_MANIFEST_PATH, {})
    model_base64 = ""
    if LOCAL_MODEL_PATH.exists():
        model_base64 = base64.b64encode(LOCAL_MODEL_PATH.read_bytes()).decode("ascii")

    return http_json(
        "POST",
        f"{api_base}/api/published/sync",
        {
            "controls": controls,
            "summary": summary,
            "manifest": manifest,
            "model_base64": model_base64,
        },
        insecure=insecure,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Poll deploy API and execute Rhino jobs locally.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8787")
    parser.add_argument("--local-api-base", default="http://127.0.0.1:8001")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for the public API. Use only for local troubleshooting.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(f"Runner polling {args.api_base} and forwarding jobs to {args.local_api_base}")

    while True:
        try:
            job = poll_next_job(args.api_base, insecure=args.insecure)
            if not job:
                if args.once:
                    return 0
                time.sleep(args.interval)
                continue

            claimed = claim_job(args.api_base, job["id"], insecure=args.insecure)
            local_result = apply_job_locally(claimed, args.local_api_base)
            if not local_result.get("ok"):
                raise RuntimeError(local_result.get("error", "Local control update failed."))
            sync_result = sync_published_outputs(args.api_base, insecure=args.insecure)
            complete_job(
                args.api_base,
                claimed["id"],
                {
                    **local_result,
                    "summary": sync_result.get("summary", local_result.get("summary")),
                    "manifest": sync_result.get("manifest"),
                    "published": {
                        "model_url": sync_result.get("model_url"),
                    },
                },
                insecure=args.insecure,
            )
        except urllib.error.URLError as error:
            print(f"[runner] network error: {error}")
            if "CERTIFICATE_VERIFY_FAILED" in str(error):
                print("[runner] hint: rerun with --insecure if you trust the API endpoint.")
        except Exception as error:
            if "claimed" in locals():
                try:
                    fail_job(args.api_base, claimed["id"], str(error), insecure=args.insecure)
                except Exception as nested:
                    print(f"[runner] failed to mark job as failed: {nested}")
            print(f"[runner] error: {error}")
        finally:
            if args.once:
                return 0
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
