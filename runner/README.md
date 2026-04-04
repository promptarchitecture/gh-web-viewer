# Runner

This folder is for the Rhino-side worker that talks to the public API.

The worker should run on the machine where Rhino and Grasshopper are available.

## Responsibility

- poll the public API queue,
- claim one job at a time,
- apply the requested value to Grasshopper,
- regenerate the published `3dm` and `summary`,
- and report completion or failure back to the API.

## Why it exists

GitHub Pages can host the web viewer, but it cannot run Rhino or Grasshopper.

The runner is the missing bridge between:

- a public website on the internet
- and the local Rhino machine that can do the actual computation

## Current status

`worker.py` is a scaffold that already knows how to:

- ask the API for the next queued job,
- claim it,
- reuse the current local bridge script,
- and mark the job complete or failed.

It is the next place to harden when moving from a single-user prototype to a real deployment.
