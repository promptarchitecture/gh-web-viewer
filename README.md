# gh-web-viewer

Grasshopper input values drive Rhino modeling, and the resulting model is exposed on the web.

## Recommended structure

- `rhino/models`
  - Store Rhino `.3dm` files here.
- `rhino/grasshopper`
  - Store Grasshopper `.gh` or `.ghx` files here.
- `rhino/assets`
  - Store referenced textures, images, CAD files, and helper assets here.
- `web`
  - Store the web viewer or control UI here.
- `docs`
  - Store workflow notes, architecture decisions, and export instructions here.
- `scripts`
  - Store local automation or conversion scripts here.
- `output`
  - Store generated exports, screenshots, and test artifacts here.

## Where to place your existing files

- Rhino file example:
  - `rhino/models/main.3dm`
- Grasshopper file example:
  - `rhino/grasshopper/main.gh`

If the Grasshopper file references external assets, move those files into `rhino/assets` and update paths to use the project folder consistently.

## Web scaffold

The `web` folder now includes a first viewer scaffold:

- `web/index.html`
- `web/styles.css`
- `web/app.js`
- `web/README.md`

It is intentionally simple:

- load a `glb` export,
- preview it in the browser,
- simulate parameter changes in the UI,
- and leave a clean place to connect a real Grasshopper execution flow later.

## GitHub Pages

This project now includes a GitHub Pages deployment workflow.

- workflow:
  - `.github/workflows/deploy-pages.yml`
- guide:
  - `docs/github-pages.md`

The workflow exports `dist-static` on GitHub Actions and deploys that bundle to Pages.

## Dynamic deployment scaffold

The next deployment step is split into two new folders:

- `api`
  - public control API scaffold
- `runner`
  - Rhino-side worker scaffold

Reference notes:

- `api/README.md`
- `runner/README.md`
- `docs/dynamic-deployment.md`
- `docs/render-deployment.md`
- `docs/operations-manual.md`
