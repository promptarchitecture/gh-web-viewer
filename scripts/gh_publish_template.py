"""Minimal template to adapt inside a Grasshopper Python 3 component.

Expected workflow:
1. Grasshopper computes geometry and summary values.
2. Another part of the definition exports the model to a temporary .3dm or .glb file.
3. This script calls publish_latest_result.py so the web viewer can pick up the latest output.
"""

from pathlib import Path
import subprocess


PROJECT_ROOT = Path("/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer")
PUBLISH_SCRIPT = PROJECT_ROOT / "scripts" / "publish_latest_result.py"
SOURCE_MODEL = PROJECT_ROOT / "rhino" / "models" / "260401_기부채납 비율 검토.3dm"
SUMMARY_JSON = PROJECT_ROOT / "output" / "latest" / "summary.json"
GH_FILE = PROJECT_ROOT / "rhino" / "grasshopper" / "260401_기부채납 비율 검토-2.gh"


def publish_latest():
    cmd = [
        "python3",
        str(PUBLISH_SCRIPT),
        "--source-model",
        str(SOURCE_MODEL),
        "--gh-file",
        str(GH_FILE),
        "--summary-json",
        str(SUMMARY_JSON),
        "--notes",
        "Published from Grasshopper Python component",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


if __name__ == "__main__":
    print(publish_latest())
