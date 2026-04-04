# Render Autofill Helper

This helper fills the current Render web-service form from the browser console.

## File

- `scripts/render_web_service_autofill.js`

## What it can fill

- Name
- Language
- Root Directory
- Build Command
- Start Command
- basic environment variable rows

## How to use

1. Open the Render web service configuration page in the browser.
2. Open DevTools.
3. Open the Console tab.
4. Paste the contents of:
   - `scripts/render_web_service_autofill.js`
5. Press Enter.
6. Then run:

```js
ghwvRenderAutofill.fillServiceForm()
```

## Current preset

- Name:
  - `gh-web-viewer-api`
- Language:
  - `Python`
- Root Directory:
  - `rhino/gh-web-viewer`
- Build Command:
  - `mkdir -p api/data`
- Start Command:
  - `python3 api/server.py`
- Environment variables:
  - `GHWV_ALLOWED_ORIGIN=https://promptarchitecture.github.io`
  - `GHWV_API_DATA_DIR=/tmp/ghwv-api-data`

## Limitation

`GHWV_PUBLIC_API_BASE_URL` should still be added after Render gives the final service URL.
