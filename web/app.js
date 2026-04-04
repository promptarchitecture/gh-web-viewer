const defaultState = {
  ratio: 40,
  height: 8,
  twist: 12,
};

const state = { ...defaultState };

const modelViewer = document.querySelector("#model-viewer");
const emptyState = document.querySelector("#empty-state");
const modelStatus = document.querySelector("#model-status");
const modelPathInput = document.querySelector("#model-path");
const parameterSummary = document.querySelector("#parameter-summary");

const ratioRange = document.querySelector("#ratio-range");
const heightRange = document.querySelector("#height-range");
const twistRange = document.querySelector("#twist-range");

const ratioValue = document.querySelector("#ratio-value");
const heightValue = document.querySelector("#height-value");
const twistValue = document.querySelector("#twist-value");

const syncLabels = () => {
  ratioValue.textContent = `${state.ratio}%`;
  heightValue.textContent = `${state.height}`;
  twistValue.textContent = `${state.twist}deg`;
  parameterSummary.textContent = `Ratio ${state.ratio}% / Height ${state.height} / Twist ${state.twist}deg`;
};

const setModelStatus = (message) => {
  modelStatus.textContent = message;
};

const showEmptyState = (visible) => {
  emptyState.hidden = !visible;
};

const loadModel = async () => {
  const src = modelPathInput.value.trim();

  if (!src) {
    setModelStatus("Missing path");
    showEmptyState(true);
    modelViewer.removeAttribute("src");
    return;
  }

  setModelStatus("Loading...");

  try {
    modelViewer.src = src;
    await modelViewer.updateComplete;
    setModelStatus("Model loaded");
    showEmptyState(false);
  } catch (error) {
    setModelStatus("Load failed");
    showEmptyState(true);
    console.error(error);
  }
};

const applyMockUpdate = () => {
  setModelStatus("Mock update applied");
  syncLabels();
};

ratioRange.addEventListener("input", (event) => {
  state.ratio = Number(event.target.value);
  syncLabels();
});

heightRange.addEventListener("input", (event) => {
  state.height = Number(event.target.value);
  syncLabels();
});

twistRange.addEventListener("input", (event) => {
  state.twist = Number(event.target.value);
  syncLabels();
});

document
  .querySelector("#load-model-button")
  .addEventListener("click", () => loadModel());

document
  .querySelector("#apply-button")
  .addEventListener("click", () => applyMockUpdate());

document.querySelector("#reset-button").addEventListener("click", () => {
  Object.assign(state, defaultState);
  ratioRange.value = String(defaultState.ratio);
  heightRange.value = String(defaultState.height);
  twistRange.value = String(defaultState.twist);
  syncLabels();
  setModelStatus("Reset complete");
});

syncLabels();
showEmptyState(true);
