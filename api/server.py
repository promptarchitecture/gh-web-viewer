#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "latest"
CONTROLS_PATH = OUTPUT_DIR / "controls.json"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    return Path(raw).expanduser() if raw else default


API_DATA_DIR = env_path("GHWV_API_DATA_DIR", PROJECT_ROOT / "api" / "data")
STATE_PATH = env_path("GHWV_STATE_PATH", API_DATA_DIR / "queue-state.json")
PUBLISHED_DIR = API_DATA_DIR / "published"
PUBLISHED_CONTROLS_PATH = PUBLISHED_DIR / "controls.json"
PUBLISHED_SUMMARY_PATH = PUBLISHED_DIR / "summary.json"
PUBLISHED_MANIFEST_PATH = PUBLISHED_DIR / "manifest.json"
PUBLISHED_MODEL_PATH = PUBLISHED_DIR / "current-preview.3dm"
PUBLIC_API_BASE_URL = os.environ.get("GHWV_PUBLIC_API_BASE_URL", "").strip()
ALLOWED_ORIGIN = os.environ.get("GHWV_ALLOWED_ORIGIN", "*").strip() or "*"


@dataclass
class Job:
    id: str
    control_id: str
    value: Any
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    error: str | None = None


def ensure_data_dir() -> None:
    API_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_controls() -> dict[str, Any]:
    return read_json(
        PUBLISHED_CONTROLS_PATH if PUBLISHED_CONTROLS_PATH.exists() else CONTROLS_PATH,
        {"title": "웹 제어 입력", "items": []},
    )


def load_summary() -> dict[str, Any]:
    return read_json(
        PUBLISHED_SUMMARY_PATH if PUBLISHED_SUMMARY_PATH.exists() else SUMMARY_PATH,
        {"title": "SUMMARY", "sections": []},
    )


def load_manifest() -> dict[str, Any]:
    return read_json(PUBLISHED_MANIFEST_PATH if PUBLISHED_MANIFEST_PATH.exists() else MANIFEST_PATH, {})


def load_state() -> dict[str, Any]:
    ensure_data_dir()
    if not STATE_PATH.exists():
        state = {"jobs": [], "active_job_id": None}
        save_state(state)
        return state
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    ensure_data_dir()
    write_json(STATE_PATH, state)


def find_job(state: dict[str, Any], job_id: str) -> dict[str, Any] | None:
    return next((job for job in state["jobs"] if job["id"] == job_id), None)


def build_public_config(host: str, port: int, request_headers: Any | None = None) -> dict[str, Any]:
    base_url = PUBLIC_API_BASE_URL

    if not base_url and request_headers is not None:
        forwarded_proto = request_headers.get("X-Forwarded-Proto", "").strip()
        host_header = request_headers.get("Host", "").strip()
        if host_header:
            scheme = forwarded_proto or "https"
            base_url = f"{scheme}://{host_header}"

    if not base_url:
        base_url = f"http://{host}:{port}"

    return {
        "mode": "dynamic_remote",
        "controls_api_url": f"{base_url}/api/controls",
        "jobs_api_url": f"{base_url}/api/jobs",
        "published_model_url": f"{base_url}/api/published/model",
        "published_summary_url": f"{base_url}/api/published/summary",
        "published_manifest_url": f"{base_url}/api/published/manifest",
        "auto_refresh_enabled": True,
    }


def publish_payload(
    payload: dict[str, Any],
    host: str,
    port: int,
    request_headers: Any | None = None,
) -> dict[str, Any]:
    ensure_data_dir()
    config = build_public_config(host, port, request_headers)

    controls = payload.get("controls") or {"title": "웹 제어 입력", "items": []}
    summary = payload.get("summary") or {"title": "SUMMARY", "sections": []}
    manifest = payload.get("manifest") or {}
    model_base64 = str(payload.get("model_base64", "")).strip()

    write_json(PUBLISHED_CONTROLS_PATH, controls)
    write_json(PUBLISHED_SUMMARY_PATH, summary)

    manifest = {
        **manifest,
        "model_path": config["published_model_url"],
        "summary_path": config["published_summary_url"],
        "updated_at": manifest.get("updated_at") or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_json(PUBLISHED_MANIFEST_PATH, manifest)

    if model_base64:
        PUBLISHED_MODEL_PATH.write_bytes(base64.b64decode(model_base64))

    return {
        "controls": controls,
        "summary": summary,
        "manifest": manifest,
        "model_url": config["published_model_url"],
    }


class DeployControlApiHandler(BaseHTTPRequestHandler):
    server_version = "GhDeployControlAPI/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def parse_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/published/model":
            if not PUBLISHED_MODEL_PATH.exists():
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(PUBLISHED_MODEL_PATH.stat().st_size))
            self.end_headers()
            return

        if path == "/api/published/summary":
            body = json.dumps(load_summary(), ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return

        if path == "/api/published/manifest":
            body = json.dumps(load_manifest(), ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return

        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "service": "gh-deploy-control-api",
                    "public_api_base_url": PUBLIC_API_BASE_URL or None,
                    "allowed_origin": ALLOWED_ORIGIN,
                    "manifest_updated_at": load_manifest().get("updated_at"),
                    "queue_size": len(load_state()["jobs"]),
                },
            )
            return

        if path == "/api/controls":
            controls = load_controls()
            summary = load_summary()
            manifest = load_manifest()
            self.send_json(
                HTTPStatus.OK,
                {
                    **controls,
                    "summary": summary,
                    "manifest": manifest,
                },
            )
            return

        if path == "/api/config":
            host, port = self.server.server_address[:2]
            self.send_json(HTTPStatus.OK, build_public_config(host, port, self.headers))
            return

        if path == "/api/published/summary":
            self.send_json(HTTPStatus.OK, load_summary())
            return

        if path == "/api/published/manifest":
            self.send_json(HTTPStatus.OK, load_manifest())
            return

        if path == "/api/published/model":
            if not PUBLISHED_MODEL_PATH.exists():
                self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Published model not found"})
                return
            self.send_bytes(HTTPStatus.OK, PUBLISHED_MODEL_PATH.read_bytes(), "application/octet-stream")
            return

        if path == "/api/jobs":
            state = load_state()
            self.send_json(
                HTTPStatus.OK,
                {
                    "items": state["jobs"],
                    "active_job_id": state.get("active_job_id"),
                },
            )
            return

        if path.startswith("/api/jobs/"):
            job_id = path.split("/")[-1]
            state = load_state()
            job = find_job(state, job_id)
            if not job:
                self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Job not found"})
                return
            self.send_json(HTTPStatus.OK, {"ok": True, "job": job})
            return

        if path == "/api/queue/next":
            state = load_state()
            next_job = next((job for job in state["jobs"] if job["status"] == "queued"), None)
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "job": next_job,
                    "active_job_id": state.get("active_job_id"),
                },
            )
            return

        self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        try:
            payload = self.parse_json_body()

            if path == "/api/jobs":
                control_id = str(payload.get("id", "")).strip()
                if not control_id:
                    raise ValueError("Missing control id.")

                control = next(
                    (item for item in load_controls().get("items", []) if item.get("id") == control_id),
                    None,
                )
                if control is None:
                    raise ValueError("Unknown control id.")

                job = Job(
                    id=str(uuid.uuid4()),
                    control_id=control_id,
                    value=payload.get("value"),
                )
                state = load_state()
                state["jobs"].append(asdict(job))
                save_state(state)
                self.send_json(HTTPStatus.ACCEPTED, {"ok": True, "job": asdict(job)})
                return

            if path == "/api/published/sync":
                host, port = self.server.server_address[:2]
                published = publish_payload(payload, host, port, self.headers)
                self.send_json(HTTPStatus.OK, {"ok": True, **published})
                return

            if path.startswith("/api/jobs/") and path.endswith("/claim"):
                job_id = path.split("/")[-2]
                state = load_state()
                job = find_job(state, job_id)
                if not job:
                    raise ValueError("Job not found.")
                if job["status"] != "queued":
                    raise ValueError("Job is not queued.")
                job["status"] = "running"
                job["updated_at"] = time.time()
                state["active_job_id"] = job_id
                save_state(state)
                self.send_json(HTTPStatus.OK, {"ok": True, "job": job})
                return

            if path.startswith("/api/jobs/") and path.endswith("/complete"):
                job_id = path.split("/")[-2]
                state = load_state()
                job = find_job(state, job_id)
                if not job:
                    raise ValueError("Job not found.")
                job["status"] = "completed"
                job["updated_at"] = time.time()
                job["result"] = payload.get("result") or {}
                state["active_job_id"] = None
                save_state(state)
                self.send_json(HTTPStatus.OK, {"ok": True, "job": job})
                return

            if path.startswith("/api/jobs/") and path.endswith("/fail"):
                job_id = path.split("/")[-2]
                state = load_state()
                job = find_job(state, job_id)
                if not job:
                    raise ValueError("Job not found.")
                job["status"] = "failed"
                job["updated_at"] = time.time()
                job["error"] = str(payload.get("error", "Worker failure"))
                state["active_job_id"] = None
                save_state(state)
                self.send_json(HTTPStatus.OK, {"ok": True, "job": job})
                return

            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
        except Exception as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve a deployable control API scaffold.")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8787")))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DeployControlApiHandler)
    print(f"Deploy control API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
