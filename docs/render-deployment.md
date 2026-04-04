# Render Deployment

This document is the easiest path to get `api/server.py` onto a public URL.

## What Render will host

Render will host:

- `api/server.py`

Render will **not** host:

- Rhino
- Grasshopper
- the local worker

Those still stay on the Rhino machine.

## Before you start

You already have:

- a GitHub repository
- a GitHub Pages frontend
- a local Rhino control bridge
- a runner scaffold

## Render setup steps

1. Go to Render and sign in.
2. Click `New +`.
3. Choose `Blueprint` or `Web Service`.
4. Connect the GitHub repository:
   - `promptarchitecture/gh-web-viewer`
5. If Render asks for a blueprint file, the repo already includes:
   - `render.yaml`

## Expected Render service settings

If you create the service manually, use:

- Runtime:
  - `Python`
- Root Directory:
  - `rhino/gh-web-viewer`
- Build Command:
  - `mkdir -p api/data`
- Start Command:
  - `python3 api/server.py`
- Health Check Path:
  - `/health`

## Required environment variables

Set these in Render:

- `GHWV_PUBLIC_API_BASE_URL`
  - example: `https://gh-web-viewer-api.onrender.com`
- `GHWV_ALLOWED_ORIGIN`
  - `https://promptarchitecture.github.io`
- `GHWV_API_DATA_DIR`
  - `/tmp/ghwv-api-data`

## After the first deploy

Open:

- `/health`
- `/api/config`
- `/api/controls`

All three should respond with JSON.

## Then update the frontend

Take the Render URL and copy it into:

- `web/site-config.production.example.json`

Specifically:

- `controls_api_url`
- `jobs_api_url`

## Important limitation for the MVP

Render is only the public queue API.

The actual Grasshopper execution still happens on the Rhino machine through:

- `scripts/gh_control_server.py`
- `runner/worker.py`

## First local-to-remote test

Once Render gives you the public API URL:

1. run the worker locally on the Rhino machine,
2. point it at the Render URL,
3. change the frontend config to the same URL,
4. test one slider,
5. verify that the job becomes `completed`.

Example worker command:

```bash
python3 /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/runner/worker.py \
  --api-base https://your-render-url.onrender.com \
  --local-api-base http://127.0.0.1:8001
```
