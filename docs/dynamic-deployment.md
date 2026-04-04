# Dynamic Deployment Plan

This document maps the current local prototype to the next deployment stages.

## What already works

- the web viewer can display the published Grasshopper result,
- the summary panel can refresh with the latest HUD-derived values,
- and a local control server can change selected Grasshopper inputs.

## What must change for public deployment

### 1. Public frontend

Host the viewer on GitHub Pages, Netlify, or Vercel.

This is already possible for the read-only static bundle.

### 2. Public control API

Run `api/server.py` on a real server.

Its job is to:

- receive control requests from the browser,
- store them as jobs,
- expose queue state,
- and return status to the frontend.

Recommended environment variables:

- `GHWV_PUBLIC_API_BASE_URL`
  - public URL of the API server
- `GHWV_ALLOWED_ORIGIN`
  - frontend origin allowed by CORS
- `GHWV_API_DATA_DIR`
  - directory used to store queue state
- `GHWV_STATE_PATH`
  - optional explicit path for the queue file

### 3. Rhino-side worker

Run `runner/worker.py` on the machine that has Rhino + Grasshopper.

Its job is to:

- poll the public API queue,
- claim one job,
- forward it into the local Grasshopper bridge,
- and mark the job complete.

### 4. Shared outputs

The viewer eventually needs public access to:

- `current-model.3dm`
- `summary.json`
- `manifest.json`

For a real deployment, those outputs should move from the local project folder to
an object store or public file bucket.

## Suggested rollout order

1. Keep GitHub Pages for the frontend.
2. Stand up `api/server.py` on a small VM or app host.
3. Keep the Rhino machine running locally.
4. Run `runner/worker.py` locally beside Rhino.
5. Change the frontend `site-config.json` to point at the public API.
6. Move outputs to a public object store.

## Production config files

- API env example:
  - `api/.env.example`
- Frontend example:
  - `web/site-config.production.example.json`

For the public frontend, the important change is:

- use `jobs_api_url` for control updates,
- keep `controls_api_url` for control metadata,
- and keep model refresh driven by `manifest.json`.

## MVP rule

Start with one Rhino machine and one queue.

Do not add multi-user concurrency logic before the single-worker flow is reliable.
