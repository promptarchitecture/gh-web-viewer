import {
  createRhinoViewerController,
  RHINO_PERSPECTIVE_VIEW,
} from "./rhino-viewer-core.js";

const statusLabel = document.querySelector("#viewer-status");
const modelInput = document.querySelector("#model-file-input");
const metaLabel = document.querySelector("#viewer-meta");
const autoRefreshToggle = document.querySelector("#auto-refresh-toggle");
const controlsTitle = document.querySelector("#controls-title");
const controlsStatus = document.querySelector("#controls-status");
const controlsList = document.querySelector("#controls-list");
const emptyState = document.querySelector("#canvas-empty-state");
const summaryPanel = document.querySelector("#summary-panel");
const summaryTitle = document.querySelector("#summary-title");
const summarySections = document.querySelector("#summary-sections");
const viewer = createRhinoViewerController({
  mountSelector: "#rhino-canvas",
  emptyStateSelector: "#canvas-empty-state",
});

const MANIFEST_PATH = "./current-manifest.json";
let autoRefreshIntervalId = null;
const SUMMARY_PATH = "./current-summary.json";
const CONTROLS_PATH = "./current-controls.json";
const SITE_CONFIG_PATH = "./site-config.json";
const DEFAULT_CONTROLS_API_URL = "http://127.0.0.1:8001/api/controls";
let lastManifestUpdatedAt = null;
let controlsConfig = null;
let siteConfig = null;
const pendingControlTimers = new Map();

const jobsAreEnabled = () => Boolean(siteConfig?.jobs_api_url);
const remotePublishedAssetsEnabled = () => siteConfig?.mode === "dynamic_remote";

const deriveApiBase = () => {
  const candidate = siteConfig?.jobs_api_url || siteConfig?.controls_api_url || "";
  if (!candidate) {
    return null;
  }

  try {
    const url = new URL(candidate);
    return url.origin;
  } catch (error) {
    console.warn("Could not derive API base from site config.", error);
    return null;
  }
};

const getPublishedModelUrl = () =>
  siteConfig?.published_model_url ||
  (deriveApiBase() ? `${deriveApiBase()}/api/published/model` : "./current-model.3dm");

const getPublishedSummaryUrl = () =>
  siteConfig?.published_summary_url ||
  (deriveApiBase() ? `${deriveApiBase()}/api/published/summary` : SUMMARY_PATH);

const getPublishedManifestUrl = () =>
  siteConfig?.published_manifest_url ||
  (deriveApiBase() ? `${deriveApiBase()}/api/published/manifest` : MANIFEST_PATH);

const setStatus = (message) => {
  statusLabel.textContent = message;
};

const setControlsStatus = (message) => {
  controlsStatus.textContent = message;
};

const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

const controlsAreEditable = () => Boolean(siteConfig?.controls_api_url || siteConfig?.jobs_api_url);

const updateControlDisplay = (controlId, value) => {
  const card = controlsList.querySelector(`[data-control-id="${controlId}"]`);
  if (!card) {
    return;
  }

  const item = controlsConfig?.items?.find((entry) => entry.id === controlId);
  if (!item) {
    return;
  }

  const valueLabel = card.querySelector(".control-value");
  if (valueLabel) {
    valueLabel.textContent = formatControlValue(item, value);
  }

  if (item.type === "toggle") {
    const button = card.querySelector(".toggle-button");
    if (button) {
      button.textContent = value ? "건축물 기부채납" : "임대주택 기부채납";
    }
  }
};

const applyRhinoPerspectiveView = () => {
  viewer.applyRhinoPerspectiveView(RHINO_PERSPECTIVE_VIEW);
  metaLabel.textContent = "Matched Rhino Perspective view";
};

const focusGhResult = () => {
  const matched = viewer.fitCameraToNamedSubset("GH_WEB_PREVIEW");
  if (!matched) {
    viewer.fitCameraToCurrentModel();
  }
  metaLabel.textContent = matched
    ? "Focused on published GH result"
    : "Focused on full published model";
};

const applyPublishedModelView = (styled) => {
  viewer.applyRhinoPerspectiveView(RHINO_PERSPECTIVE_VIEW);
  metaLabel.textContent = `Matched Rhino Perspective view / Styled ${styled} objects`;
};

const renderSummary = (summary) => {
  if (!summary || !Array.isArray(summary.sections) || summary.sections.length === 0) {
    summaryPanel.hidden = true;
    summarySections.innerHTML = "";
    return;
  }

  summaryTitle.textContent = summary.title || "SUMMARY";
  summarySections.innerHTML = summary.sections
    .map((section) => {
      const items = Array.isArray(section.items) ? section.items : [];
      const itemMarkup = items
        .map(
          (item) => `
            <div class="summary-item">
              <span>${item.label || ""}</span>
              <strong>${item.value || ""}</strong>
            </div>
          `,
        )
        .join("");

      return `
        <section class="summary-section">
          ${section.heading ? `<p class="summary-heading">${section.heading}</p>` : ""}
          ${itemMarkup}
        </section>
      `;
    })
    .join("");

  summaryPanel.hidden = false;
};

const formatControlValue = (item, value) => {
  if (item.type === "toggle") {
    return value ? "True" : "False";
  }

  const step = Number(item.step ?? 1);
  if (Number.isInteger(step)) {
    return String(Math.round(Number(value)));
  }

  return String(value);
};

const renderControls = (config) => {
  const items = Array.isArray(config?.items) ? config.items : [];
  controlsConfig = config;
  controlsTitle.textContent = config?.title || "웹 제어 입력";

  if (items.length === 0) {
    controlsList.innerHTML = "";
    setControlsStatus("Empty");
    return;
  }

  controlsList.innerHTML = items
    .map((item) => {
      if (item.type === "toggle") {
        const current = Boolean(item.value);
        return `
          <div class="control-card toggle-card" data-control-id="${item.id}">
            <label>
              <span>${item.label}</span>
              <span class="control-value">${current ? "True" : "False"}</span>
            </label>
            <button class="ghost-button toggle-button" type="button" ${controlsAreEditable() ? "" : "disabled"}>
              ${current ? "건축물 기부채납" : "임대주택 기부채납"}
            </button>
            <p class="toggle-hint">${item.false_label || ""}\n${item.true_label || ""}</p>
          </div>
        `;
      }

      return `
        <div class="control-card" data-control-id="${item.id}">
          <label>
            <span>${item.label}</span>
            <span class="control-value">${formatControlValue(item, item.value)}</span>
          </label>
          <input
            type="range"
            min="${item.min}"
            max="${item.max}"
            step="${item.step}"
            value="${item.value}"
            ${controlsAreEditable() ? "" : "disabled"}
          />
        </div>
      `;
    })
    .join("");

  setControlsStatus(controlsAreEditable() ? "Connected" : "Read-only");
  bindControlEvents();
};

const loadControls = async () => {
  try {
    setControlsStatus("Loading");
    const staticResponse = await fetch(`${CONTROLS_PATH}?t=${Date.now()}`);
    if (!staticResponse.ok) {
      throw new Error(`Static controls request failed: ${staticResponse.status}`);
    }

    const staticConfig = await staticResponse.json();
    renderControls(staticConfig);

    if (siteConfig?.controls_api_url) {
      try {
        const apiResponse = await fetch(`${siteConfig.controls_api_url}?t=${Date.now()}`);
        if (!apiResponse.ok) {
          throw new Error(`Controls API request failed: ${apiResponse.status}`);
        }
        const liveConfig = await apiResponse.json();
        renderControls(liveConfig);
      } catch (apiError) {
        console.warn("Controls API unavailable, keeping static controls visible.", apiError);
        siteConfig = { ...siteConfig, controls_api_url: null };
        renderControls(staticConfig);
      }
    }
  } catch (error) {
    console.error(error);
    controlsList.innerHTML = "";
    setControlsStatus("Load failed");
  }
};

const postControlUpdate = async (controlId, value) => {
  if (jobsAreEnabled()) {
    const response = await fetch(siteConfig.jobs_api_url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id: controlId, value }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      throw new Error(payload.error || `HTTP ${response.status}`);
    }

    const payload = await response.json();
    const jobId = payload?.job?.id;
    if (!jobId) {
      throw new Error("Queued job response did not include a job id.");
    }

    setControlsStatus("Queued");

    const startedAt = Date.now();
    while (Date.now() - startedAt < 30000) {
      await wait(500);

      const jobResponse = await fetch(`${siteConfig.jobs_api_url}/${jobId}?t=${Date.now()}`);
      if (!jobResponse.ok) {
        throw new Error(`Job status request failed: ${jobResponse.status}`);
      }

      const jobPayload = await jobResponse.json();
      const job = jobPayload?.job;
      if (!job) {
        throw new Error("Job status payload is missing the job object.");
      }

      if (job.status === "completed") {
        return job.result || { ok: true };
      }

      if (job.status === "failed") {
        throw new Error(job.error || "Queued job failed.");
      }

      setControlsStatus(job.status === "running" ? "Applying" : "Queued");
    }

    throw new Error("Timed out waiting for Grasshopper update.");
  }

  const response = await fetch(siteConfig.controls_api_url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id: controlId, value }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    throw new Error(payload.error || `HTTP ${response.status}`);
  }

  return response.json();
};

const queueControlUpdate = (controlId, value, delay = 180) => {
  if (pendingControlTimers.has(controlId)) {
    window.clearTimeout(pendingControlTimers.get(controlId));
  }

  updateControlDisplay(controlId, value);
  setControlsStatus("Applying");

  const timerId = window.setTimeout(async () => {
    pendingControlTimers.delete(controlId);

    try {
      const payload = await postControlUpdate(controlId, value);
      const control = payload.control;
      const item = controlsConfig?.items?.find((entry) => entry.id === controlId);
      if (item && control) {
        item.value = control.value;
        updateControlDisplay(controlId, control.value);
      }
      if (payload.summary) {
        renderSummary(payload.summary);
      }
      await wait(350);
      await loadPublishedModel({ preserveStatus: true });
      setControlsStatus("Applied");
    } catch (error) {
      console.error(error);
      setControlsStatus("Apply failed");
    }
  }, delay);

  pendingControlTimers.set(controlId, timerId);
};

const bindControlEvents = () => {
  if (!controlsAreEditable()) {
    return;
  }

  controlsList.querySelectorAll(".control-card").forEach((card) => {
    const controlId = card.dataset.controlId;
    const item = controlsConfig?.items?.find((entry) => entry.id === controlId);
    if (!item) {
      return;
    }

    if (item.type === "toggle") {
      const button = card.querySelector(".toggle-button");
      button?.addEventListener("click", () => {
        const nextValue = !Boolean(item.value);
        item.value = nextValue;
        queueControlUpdate(controlId, nextValue, 0);
      });
      return;
    }

    const input = card.querySelector('input[type="range"]');
    if (!input) {
      return;
    }

    input.addEventListener("input", (event) => {
      const nextValue = Number(event.target.value);
      item.value = nextValue;
      updateControlDisplay(controlId, nextValue);
      queueControlUpdate(controlId, nextValue, 180);
    });

    input.addEventListener("change", (event) => {
      const nextValue = Number(event.target.value);
      item.value = nextValue;
      queueControlUpdate(controlId, nextValue, 0);
    });
  });
};

const loadSiteConfig = async () => {
  try {
    const response = await fetch(`${SITE_CONFIG_PATH}?t=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`Site config request failed: ${response.status}`);
    }
    siteConfig = await response.json();
  } catch (error) {
    console.warn("Falling back to local interactive config.", error);
    siteConfig = {
      mode: "local_interactive",
      controls_api_url: DEFAULT_CONTROLS_API_URL,
      jobs_api_url: null,
      auto_refresh_enabled: true,
    };
  }
};

const loadSummary = async () => {
  try {
    const response = await fetch(`${getPublishedSummaryUrl()}?t=${Date.now()}`);
    if (!response.ok) {
      throw new Error(`Summary request failed: ${response.status}`);
    }
    const summary = await response.json();
    renderSummary(summary);
  } catch (error) {
    console.error(error);
    renderSummary(null);
  }
};

const loadPublishedModel = async ({ preserveStatus = false } = {}) => {
  const rawPath = getPublishedModelUrl();
  const requestPath = `${rawPath}?t=${Date.now()}`;

  if (!preserveStatus) {
    setStatus("Loading 3DM...");
    metaLabel.textContent = `Requesting ${rawPath}`;
  }

  await viewer.loadModel(requestPath);
  if (emptyState) {
    emptyState.hidden = true;
  }
  const styled = viewer.stylePublishedModel();
  await loadSummary();
  applyPublishedModelView(styled);
  setStatus("3DM loaded");
};

const readManifest = async () => {
  const response = await fetch(`${getPublishedManifestUrl()}?t=${Date.now()}`);
  if (!response.ok) {
    throw new Error(`Manifest request failed: ${response.status}`);
  }
  return response.json();
};

const loadModel = async () => {
  const rawPath = modelInput.value.trim();

  if (!rawPath) {
    setStatus("Missing path");
    return;
  }

  setStatus("Loading 3DM...");
  metaLabel.textContent = `Requesting ${rawPath}`;

  try {
    const isPublishedGhModel =
      rawPath.includes("current-model.3dm") ||
      rawPath.includes("current-preview.3dm") ||
      rawPath.includes("/api/published/model");
    if (isPublishedGhModel) {
      await loadPublishedModel({ preserveStatus: true });
    } else {
      const requestPath = rawPath.includes("?")
        ? `${rawPath}&t=${Date.now()}`
        : `${rawPath}?t=${Date.now()}`;
      await viewer.loadModel(requestPath);
      if (emptyState) {
        emptyState.hidden = true;
      }
      applyRhinoPerspectiveView();
      setStatus("3DM loaded");
    }
  } catch (error) {
    console.error(error);
    setStatus("Load failed");
    metaLabel.textContent = `Could not load ${rawPath}. Check the local file path and viewer setup.`;
  }
};

const syncAutoRefresh = () => {
  if (autoRefreshIntervalId) {
    window.clearInterval(autoRefreshIntervalId);
    autoRefreshIntervalId = null;
  }

  if (autoRefreshToggle.checked) {
    autoRefreshIntervalId = window.setInterval(async () => {
      try {
        const manifest = await readManifest();
        const updatedAt = manifest.updated_at || null;

        if (!updatedAt) {
          return;
        }

        if (lastManifestUpdatedAt === null) {
          lastManifestUpdatedAt = updatedAt;
          return;
        }

        if (updatedAt !== lastManifestUpdatedAt) {
          modelInput.value = remotePublishedAssetsEnabled()
            ? getPublishedModelUrl()
            : "./current-model.3dm";
          await loadPublishedModel({ preserveStatus: true });
          lastManifestUpdatedAt = updatedAt;
          metaLabel.textContent = `Matched Rhino Perspective view / Auto-updated ${updatedAt}`;
        }
      } catch (error) {
        console.error(error);
      }
    }, 1000);
  }
};

const initViewer = async () => {
  setStatus("Loading viewer libs...");

  try {
    await viewer.init();
    await loadSiteConfig();
    document
      .querySelector("#load-3dm-button")
      .addEventListener("click", () => loadModel());
    document
      .querySelector("#rhino-view-button")
      .addEventListener("click", applyRhinoPerspectiveView);
    document.querySelector("#fit-gh-button").addEventListener("click", focusGhResult);
    autoRefreshToggle.addEventListener("change", syncAutoRefresh);
    autoRefreshToggle.checked = siteConfig.auto_refresh_enabled !== false;
    if (!controlsAreEditable()) {
      autoRefreshToggle.checked = false;
    }

    setStatus("Viewer ready");
    await loadControls();
    if (remotePublishedAssetsEnabled()) {
      modelInput.value = getPublishedModelUrl();
    }
    await loadModel();
    try {
      const manifest = await readManifest();
      lastManifestUpdatedAt = manifest.updated_at || null;
    } catch (error) {
      console.error(error);
    }
    syncAutoRefresh();
  } catch (error) {
    console.error(error);
    setStatus("Viewer lib load failed");
    metaLabel.textContent =
      "The browser could not load the local viewer libraries. Reload once, and if it persists check the console.";
  }
};

initViewer();
