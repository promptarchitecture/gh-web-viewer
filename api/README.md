# API

This folder is the public control layer for a deployed version of the viewer.

It is intentionally separate from `scripts/gh_control_server.py`.

- `scripts/gh_control_server.py`
  - local-only bridge used on the Rhino machine today
- `api/server.py`
  - internet-facing control API scaffold
- `runner/worker.py`
  - Rhino-side worker that pulls jobs from the API and executes them locally

## Planned flow

1. Browser sends a control change to `POST /api/jobs`
2. API stores the request in a queue
3. Rhino worker polls the queue
4. Worker applies the change to Grasshopper
5. Worker republishes the latest model and summary
6. Worker reports job completion back to the API
7. Browser sees the new manifest timestamp and reloads the model

## Current status

The files in this folder are a deployment scaffold.

They provide:

- a stable public API shape,
- a simple queue model,
- a health endpoint,
- and an interface the Rhino worker can start using.

They do not replace the current local control server yet.
