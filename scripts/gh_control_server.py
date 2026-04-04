#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from rhino.scripts.gh_component_bridge import send_command


OUTPUT_DIR = PROJECT_ROOT / "output" / "latest"
CONTROLS_PATH = OUTPUT_DIR / "controls.json"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"
HUD_MERGE_GUID = "c208f853-6fa5-40b6-a749-26363b9e3254"


def load_controls() -> dict[str, Any]:
    if not CONTROLS_PATH.exists():
        return {"title": "웹 제어 입력", "items": []}
    return json.loads(CONTROLS_PATH.read_text(encoding="utf-8"))


def save_controls(config: dict[str, Any]) -> None:
    CONTROLS_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_set_control_code(control_id: str, value: Any) -> str:
    payload = json.dumps({"id": control_id, "value": value}, ensure_ascii=False)
    return f"""
import json
import Rhino
Rhino.RhinoApp.RunScript("_Grasshopper", False)
import Grasshopper
import System

request = json.loads(r'''{payload}''')
result = {{"ok": False, "requested": request}}

canvas = Grasshopper.Instances.ActiveCanvas
doc = canvas.Document if canvas else None
if doc is None:
    result["error"] = "Active Grasshopper document not found."
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit

gid = System.Guid(request["id"])
obj = None
for candidate in doc.Objects:
    if candidate.InstanceGuid == gid:
        obj = candidate
        break

if obj is None:
    result["error"] = "Target control not found in active GH document."
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit

typename = str(obj.GetType().FullName)
result["control_type"] = typename

if typename == "Grasshopper.Kernel.Special.GH_NumberSlider":
    decimal_value = System.Decimal.Parse(str(request["value"]))
    obj.SetSliderValue(decimal_value)
    result["value"] = float(obj.CurrentValue)
elif typename == "Grasshopper.Kernel.Special.GH_BooleanToggle":
    obj.Value = bool(request["value"])
    result["value"] = bool(obj.Value)
else:
    result["error"] = "Unsupported control type: " + typename
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit

obj.ExpireSolution(False)
doc.NewSolution(True)
result["ok"] = True
print(json.dumps(result, ensure_ascii=False))
"""


def build_summary_fetch_code() -> str:
    return f"""
import json
import Rhino
Rhino.RhinoApp.RunScript("_Grasshopper", False)
import Grasshopper
import System

result = {{"ok": False, "lines": []}}
canvas = Grasshopper.Instances.ActiveCanvas
doc = canvas.Document if canvas else None
if doc is None:
    result["error"] = "Active Grasshopper document not found."
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit

merge_guid = System.Guid("{HUD_MERGE_GUID}")
merge = None
for candidate in doc.Objects:
    if candidate.InstanceGuid == merge_guid:
        merge = candidate
        break

if merge is None:
    result["error"] = "HUD merge component not found."
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit

lines = []
for param in merge.Params.Input:
    try:
        branch = param.VolatileData.get_Branch(0)
    except Exception:
        branch = None
    if branch is None or branch.Count == 0:
        continue
    for item in branch:
        try:
            value = item.ScriptVariable()
        except Exception:
            value = None
        text = str(value if value is not None else item).strip()
        if text:
            lines.append(text)

result["ok"] = True
result["lines"] = lines
print(json.dumps(result, ensure_ascii=False))
"""


def run_rhino_control_update(control_id: str, value: Any) -> dict[str, Any]:
    resp = send_command(
        "127.0.0.1",
        1999,
        "execute_rhinoscript_python_code",
        {"code": build_set_control_code(control_id, value)},
    )
    if resp.get("status") != "success":
        raise RuntimeError(f"RhinoMCP request failed: {resp}")

    raw = resp.get("result", {}).get("result", "")
    marker = "Print output:"
    payload = raw.split(marker, 1)[1].strip() if marker in raw else raw.strip()
    return json.loads(payload)


def fetch_rhino_summary_lines() -> list[str]:
    resp = send_command(
        "127.0.0.1",
        1999,
        "execute_rhinoscript_python_code",
        {"code": build_summary_fetch_code()},
    )
    if resp.get("status") != "success":
        raise RuntimeError(f"RhinoMCP summary request failed: {resp}")

    raw = resp.get("result", {}).get("result", "")
    marker = "Print output:"
    payload = raw.split(marker, 1)[1].strip() if marker in raw else raw.strip()
    parsed = json.loads(payload)
    if not parsed.get("ok"):
        raise RuntimeError(parsed.get("error", "Summary fetch failed."))
    return list(parsed.get("lines", []))


def build_summary_payload(lines: list[str]) -> dict[str, Any]:
    title = "SUMMARY"
    sections: list[dict[str, Any]] = []
    current_items: list[dict[str, str]] = []

    for line in lines:
        text = line.strip()
        if not text:
            continue
        if text.upper() == "SUMMARY":
            title = text
            continue
        if set(text) == {"-"}:
            if current_items:
                sections.append({"items": current_items})
                current_items = []
            continue

        if "[" in text and text.endswith("]"):
            label, value = text.rsplit("[", 1)
            current_items.append(
                {
                    "label": label.strip(),
                    "value": value[:-1].strip(),
                }
            )
        else:
            current_items.append({"label": text, "value": ""})

    if current_items:
        sections.append({"items": current_items})

    return {"title": title, "sections": sections}


def refresh_summary_json() -> dict[str, Any]:
    lines = fetch_rhino_summary_lines()
    payload = build_summary_payload(lines)
    SUMMARY_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def normalize_value(item: dict[str, Any], incoming: Any) -> Any:
    if item.get("type") == "toggle":
        if isinstance(incoming, bool):
            return incoming
        if isinstance(incoming, str):
            return incoming.strip().lower() in {"1", "true", "yes", "on"}
        return bool(incoming)

    value = float(incoming)
    minimum = float(item["min"])
    maximum = float(item["max"])
    step = float(item.get("step", 1))
    value = min(max(value, minimum), maximum)
    ticks = round((value - minimum) / step)
    snapped = minimum + ticks * step
    decimals = max(0, len(str(step).split(".")[1]) if "." in str(step) else 0)
    snapped = round(snapped, decimals)
    if decimals == 0:
        return int(snapped)
    return snapped


class GhControlHandler(BaseHTTPRequestHandler):
    server_version = "GhControlHTTP/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
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

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/controls":
            self.send_json(HTTPStatus.OK, load_controls())
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/controls":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            control_id = str(payload.get("id", "")).strip()
            incoming_value = payload.get("value")
            if not control_id:
                raise ValueError("Missing control id.")

            config = load_controls()
            items = config.get("items", [])
            item = next((entry for entry in items if entry.get("id") == control_id), None)
            if item is None:
                raise ValueError("Control not found in controls.json.")

            normalized = normalize_value(item, incoming_value)
            result = run_rhino_control_update(control_id, normalized)
            if not result.get("ok"):
                raise RuntimeError(result.get("error", "Rhino update failed."))

            summary = refresh_summary_json()

            item["value"] = result.get("value", normalized)
            save_controls(config)
            self.send_json(
                HTTPStatus.OK,
                {"ok": True, "control": item, "rhino": result, "summary": summary},
            )
        except Exception as error:
            self.send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": str(error)},
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve a local API for web -> Grasshopper controls.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    server = ThreadingHTTPServer((args.host, args.port), GhControlHandler)
    print(f"GH control server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
