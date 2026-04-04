# Publish Scripts

## Purpose

These scripts publish the latest Grasshopper result into a stable web-facing contract.

## Main script

- `publish_latest_result.py`
  - Copies the latest model into `output/latest`
  - Optionally copies `summary.json`
  - Rewrites `output/latest/manifest.json`

Example:

```bash
cd /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/scripts
python3 publish_latest_result.py \
  --source-model ../rhino/models/260401_기부채납\ 비율\ 검토.3dm \
  --gh-file ../rhino/grasshopper/260401_기부채납\ 비율\ 검토-2.gh \
  --summary-json ../output/latest/summary.json
```

## Grasshopper integration idea

- Export the current result to a `.3dm` or `.glb`
- Update `summary.json`
- Call `publish_latest_result.py`
- Let `web/gh-live.html` auto-refresh the result
