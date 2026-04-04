# Web Viewer Scaffold

This folder contains the first web scaffold for the Rhino and Grasshopper project.

## Included files

- `index.html`
  - Viewer shell and parameter UI
- `live-view.html`
  - Page for showing the latest Rhino viewport image
- `rhino-viewer.html`
  - Interactive browser viewer for the Rhino `.3dm` file
- `gh-live.html`
  - Manifest-driven page for the latest Grasshopper export
- `styles.css`
  - Layout and visual styling
- `app.js`
  - Local state and mock interactions
- `live-view.js`
  - Refresh logic for the viewport image page
- `rhino-viewer.js`
  - Three.js-based `.3dm` loader and camera controls
- `rhino-viewer-core.js`
  - Shared Rhino viewer controller used by multiple pages
- `gh-live.js`
  - Polls the latest export manifest and reloads the newest result

## Current behavior

- Loads a `glb` model path into a web viewer.
- Shows placeholder Grasshopper parameters in the side panel.
- Lets you simulate a parameter update without a backend.
- Displays the latest exported Rhino viewport image on a separate page.
- Loads the Rhino `.3dm` model directly in the browser for interactive orbit and zoom.
- Includes a manifest-based page for future Grasshopper result refreshes.

## What to do next

1. Export a Rhino result to `glb`.
2. Place the exported file somewhere reachable by the web app.
3. Update the `GLB Path` field and verify the viewer loads.
4. Replace the mock update in `app.js` with a real request to Rhino Compute, Hops, or another Grasshopper bridge.
5. Save Rhino viewport snapshots as `output/viewport-latest.png` to display them on `live-view.html`.
6. Open `rhino-viewer.html` to inspect the current `.3dm` file directly on the web.
7. Open `gh-live.html` to use the future Grasshopper export pipeline based on `output/latest/manifest.json`.

## Local preview

You can preview this with any simple static server.

Example:

```bash
cd /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/web
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Static export

To create a deployable static bundle with real files instead of local symlinks:

```bash
python3 /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/scripts/export_static_site.py
```

This creates:

- `/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/dist-static`

The exported bundle is safe for static hosting because it includes:

- `current-model.3dm`
- `current-manifest.json`
- `current-summary.json`
- `current-controls.json`
- `site-config.json`

In the static export, controls are shown as read-only and the model is not auto-refreshed from a local API.
