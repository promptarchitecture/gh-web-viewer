#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web"
OUTPUT_DIR = PROJECT_ROOT / "output" / "latest"
DIST_DIR = PROJECT_ROOT / "dist-static"

COPY_FILES = [
    "rhino-viewer.html",
    "rhino-viewer.js",
    "rhino-viewer-core.js",
    "styles.css",
    "README.md",
]


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def export_static_site(destination: Path) -> Path:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for name in COPY_FILES:
        copy_file(WEB_DIR / name, destination / name)

    # GitHub Pages opens the repository root URL with index.html.
    copy_file(WEB_DIR / "rhino-viewer.html", destination / "index.html")

    vendor_src = WEB_DIR / "vendor"
    if vendor_src.exists():
        shutil.copytree(vendor_src, destination / "vendor")

    assets = {
        OUTPUT_DIR / "current-preview.3dm": destination / "current-model.3dm",
        OUTPUT_DIR / "manifest.json": destination / "current-manifest.json",
        OUTPUT_DIR / "summary.json": destination / "current-summary.json",
        OUTPUT_DIR / "controls.json": destination / "current-controls.json",
    }
    for source, target in assets.items():
        copy_file(source, target)

    config = {
        "mode": "static_export",
        "controls_api_url": None,
        "auto_refresh_enabled": False,
        "generated_from": str(PROJECT_ROOT),
    }
    (destination / "site-config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a static deployment bundle for the GH web viewer.")
    parser.add_argument(
        "--output",
        default=str(DIST_DIR),
        help="Destination folder for the static export bundle.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    destination = Path(args.output).expanduser().resolve()
    export_static_site(destination)
    print(f"Static export ready -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
