const image = document.querySelector("#viewport-image");
const status = document.querySelector("#image-status");
const timestampLabel = document.querySelector("#timestamp-label");
const refreshButton = document.querySelector("#refresh-button");
const autoRefresh = document.querySelector("#auto-refresh");

let intervalId = null;

const setStatus = (message) => {
  status.textContent = message;
};

const refreshImage = () => {
  const basePath = "../output/viewport-latest.png";
  const nextSrc = `${basePath}?t=${Date.now()}`;

  image.onload = () => {
    setStatus("Image loaded");
    timestampLabel.textContent = `Last refresh ${new Date().toLocaleTimeString()}`;
  };

  image.onerror = () => {
    setStatus("Snapshot missing");
    timestampLabel.textContent = "Export a Rhino viewport image to output/viewport-latest.png";
  };

  setStatus("Refreshing...");
  image.src = nextSrc;
};

const syncAutoRefresh = () => {
  if (intervalId) {
    window.clearInterval(intervalId);
    intervalId = null;
  }

  if (autoRefresh.checked) {
    intervalId = window.setInterval(refreshImage, 3000);
  }
};

refreshButton.addEventListener("click", refreshImage);
autoRefresh.addEventListener("change", syncAutoRefresh);

refreshImage();
syncAutoRefresh();
