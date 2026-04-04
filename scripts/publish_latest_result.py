#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish the latest Grasshopper result for the web viewer."
    )
    parser.add_argument("--source-model", required=True, help="Path to the source 3dm or glb file")
    parser.add_argument("--output-dir", default="../output/latest", help="Output folder for manifest and assets")
    parser.add_argument("--gh-file", default="", help="Path to the source .gh file")
    parser.add_argument("--summary-json", default="", help="Optional path to a summary JSON file")
    parser.add_argument("--notes", default="Latest Grasshopper solution exported for web preview")
    parser.add_argument("--camera-mode", default="rhino_perspective")
    parser.add_argument("--timestamp", default="", help="Optional ISO timestamp override")
    return parser


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def copy_if_needed(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        if target.exists() and source.samefile(target):
            return
    except FileNotFoundError:
        pass

    if target.exists() or target.is_symlink():
        target.unlink()

    shutil.copy2(source, target)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    output_dir = (script_dir / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_model = Path(args.source_model).expanduser().resolve()
    if not source_model.exists():
      raise FileNotFoundError(f"Source model not found: {source_model}")

    model_ext = source_model.suffix.lower()
    if model_ext not in {".3dm", ".glb"}:
        raise ValueError(f"Unsupported model format: {model_ext}")

    target_model = output_dir / f"current-model{model_ext}"
    copy_if_needed(source_model, target_model)

    manifest: dict[str, object] = {
        "version": 1,
        "updated_at": args.timestamp or iso_now(),
        "format": model_ext.lstrip("."),
        "model_path": f"../output/latest/{target_model.name}",
        "source": {
            "gh_file": args.gh_file,
            "notes": args.notes,
        },
        "camera": {
            "mode": args.camera_mode,
        },
    }

    if args.summary_json:
        summary_source = Path(args.summary_json).expanduser().resolve()
        if not summary_source.exists():
            raise FileNotFoundError(f"Summary JSON not found: {summary_source}")
        target_summary = output_dir / "summary.json"
        copy_if_needed(summary_source, target_summary)
        manifest["summary_path"] = "../output/latest/summary.json"

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Published model -> {target_model}")
    if args.summary_json:
        print(f"Published summary -> {output_dir / 'summary.json'}")
    print(f"Published manifest -> {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
