# Grasshopper Web Pipeline

## Goal

Show Grasshopper-driven modeling on the web without relying on baked Rhino objects as the primary workflow.

## Recommended MVP pipeline

1. Grasshopper computes the latest result.
2. The result is exported to a web-readable file.
3. A small manifest file is updated with the latest result path and metadata.
4. The web page polls the manifest and reloads the latest result.

## Why this is the right intermediate step

- It keeps Grasshopper as the source of truth.
- It avoids locking the workflow to one baked Rhino snapshot.
- It gives the web app a stable contract before live parameter editing is added.

## File contract

Output folder:

- `output/latest/manifest.json`
- `output/latest/current-model.3dm` or `output/latest/current-model.glb`

Example manifest:

```json
{
  "version": 1,
  "updated_at": "2026-04-02T01:00:00+09:00",
  "format": "3dm",
  "model_path": "../output/latest/current-model.3dm",
  "source": {
    "gh_file": "../rhino/grasshopper/260401_기부채납 비율 검토-2.gh",
    "notes": "Latest Grasshopper solution exported for web preview"
  },
  "camera": {
    "mode": "rhino_perspective"
  }
}
```

## Export strategy

Short term:

- Export `3dm` after each important Grasshopper update.
- Web viewer reloads the latest `3dm`.

Mid term:

- Export `glb` for cleaner web rendering and easier material control.
- Keep summary numbers as separate JSON data.

## Important note about Grasshopper preview

Grasshopper preview graphics are not the same thing as persisted Rhino objects.
If a result only exists as viewport preview, the web viewer cannot read it from the Rhino file directly.

That means the live system must explicitly export the latest result each time.

## Next implementation target

1. Grasshopper writes `output/latest/manifest.json`
2. Grasshopper writes `output/latest/current-model.3dm` or `current-model.glb`
3. Web page polls the manifest every few seconds
4. Web page reloads when `updated_at` changes
