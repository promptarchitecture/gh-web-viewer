import {
  createRhinoViewerController,
  RHINO_PERSPECTIVE_VIEW,
} from "./rhino-viewer-core.js";

const manifestStatus = document.querySelector("#manifest-status");
const manifestMeta = document.querySelector("#manifest-meta");
const resultSummary = document.querySelector("#result-summary");
const manifestPathInput = document.querySelector("#manifest-path-input");
const refreshButton = document.querySelector("#refresh-manifest-button");
const autoRefreshCheckbox = document.querySelector("#manifest-auto-refresh");
const summaryPanel = document.querySelector("#summary-panel");
const summaryTitle = document.querySelector("#summary-title");
const summarySections = document.querySelector("#summary-sections");

let lastUpdatedAt = null;
let intervalId = null;

const viewer = createRhinoViewerController({
  mountSelector: "#rhino-canvas",
  emptyStateSelector: "#canvas-empty-state",
});

const setStatus = (message) => {
  manifestStatus.textContent = message;
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

const readManifest = async () => {
  const rawPath = manifestPathInput.value.trim();

  if (!rawPath) {
    setStatus("Missing manifest path");
    return;
  }

  try {
    setStatus("Loading manifest...");
    const response = await fetch(`${rawPath}?t=${Date.now()}`);

    if (!response.ok) {
      throw new Error(`Manifest request failed: ${response.status}`);
    }

    const manifest = await response.json();
    const updatedAt = manifest.updated_at || "(unknown time)";
    const format = manifest.format || "unknown";
    const notes = manifest.source?.notes || "No notes";
    const modelPath = manifest.model_path;
    const summaryPath = manifest.summary_path;

    manifestMeta.textContent = `${notes} / Updated ${updatedAt}`;
    resultSummary.textContent = `${format.toUpperCase()} / ${updatedAt}`;

    if (!modelPath) {
      setStatus("Manifest missing model");
      return;
    }

    if (lastUpdatedAt !== updatedAt) {
      setStatus("Loading latest model...");
      await viewer.loadModel(modelPath);

      if (manifest.camera?.mode === "rhino_perspective") {
        viewer.applyRhinoPerspectiveView(RHINO_PERSPECTIVE_VIEW);
      }
    }

    if (summaryPath) {
      const summaryResponse = await fetch(`${summaryPath}?t=${Date.now()}`);
      if (!summaryResponse.ok) {
        throw new Error(`Summary request failed: ${summaryResponse.status}`);
      }
      const summary = await summaryResponse.json();
      renderSummary(summary);
    } else {
      renderSummary(null);
    }

    lastUpdatedAt = updatedAt;
    setStatus("Watching latest result");
  } catch (error) {
    console.error(error);
    setStatus("Manifest load failed");
    manifestMeta.textContent =
      "Could not read the manifest. Check the file path and JSON structure.";
    renderSummary(null);
  }
};

const syncAutoRefresh = () => {
  if (intervalId) {
    window.clearInterval(intervalId);
    intervalId = null;
  }

  if (autoRefreshCheckbox.checked) {
    intervalId = window.setInterval(readManifest, 3000);
  }
};

refreshButton.addEventListener("click", readManifest);
autoRefreshCheckbox.addEventListener("change", syncAutoRefresh);

await viewer.init();
readManifest();
syncAutoRefresh();
