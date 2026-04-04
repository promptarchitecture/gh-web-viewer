(() => {
  const preset = {
    name: "gh-web-viewer-api",
    branch: "main",
    region: "Oregon (US West)",
    rootDirectory: "rhino/gh-web-viewer",
    buildCommand: "mkdir -p api/data",
    startCommand: "python3 api/server.py",
    envVars: [
      ["GHWV_ALLOWED_ORIGIN", "https://promptarchitecture.github.io"],
      ["GHWV_API_DATA_DIR", "/tmp/ghwv-api-data"],
    ],
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const fireEvents = (el) => {
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    el.dispatchEvent(new Event("blur", { bubbles: true }));
  };

  const visibleText = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();

  const allInputs = () =>
    Array.from(document.querySelectorAll("input, textarea, select")).filter(
      (el) => el.offsetParent !== null
    );

  const fieldByLabel = (labelText) => {
    const labels = Array.from(document.querySelectorAll("label, p, div, span, h1, h2, h3"));
    for (const label of labels) {
      if (!visibleText(label).includes(labelText)) continue;

      const forId = label.getAttribute?.("for");
      if (forId) {
        const direct = document.getElementById(forId);
        if (direct) return direct;
      }

      const wrapper = label.closest("div, section, form");
      if (wrapper) {
        const candidate = wrapper.querySelector("input, textarea, select");
        if (candidate) return candidate;
      }
    }
    return null;
  };

  const setTextField = (labelText, value) => {
    const field = fieldByLabel(labelText);
    if (!field) {
      console.warn(`[ghwv] Could not find field for label: ${labelText}`);
      return false;
    }
    field.focus();
    field.value = value;
    fireEvents(field);
    return true;
  };

  const setSelectLikeField = async (labelText, desiredText) => {
    const field = fieldByLabel(labelText);
    if (!field) {
      console.warn(`[ghwv] Could not find select field for label: ${labelText}`);
      return false;
    }

    if (field.tagName === "SELECT") {
      const option = Array.from(field.options).find((item) => visibleText(item).includes(desiredText));
      if (!option) {
        console.warn(`[ghwv] Could not find option "${desiredText}" for ${labelText}`);
        return false;
      }
      field.value = option.value;
      fireEvents(field);
      return true;
    }

    field.click();
    await sleep(300);

    const option = Array.from(document.querySelectorAll('[role="option"], li, div, span')).find((el) =>
      visibleText(el).includes(desiredText)
    );
    if (!option) {
      console.warn(`[ghwv] Could not find popup option "${desiredText}" for ${labelText}`);
      return false;
    }
    option.click();
    return true;
  };

  const clickButtonByText = async (text) => {
    const button = Array.from(document.querySelectorAll("button, a")).find((el) =>
      visibleText(el).includes(text)
    );
    if (!button) {
      console.warn(`[ghwv] Could not find button: ${text}`);
      return false;
    }
    button.click();
    await sleep(300);
    return true;
  };

  const fillEnvVars = async () => {
    for (const [key, value] of preset.envVars) {
      const existingKey = Array.from(allInputs()).find((el) => el.value === key);
      if (existingKey) continue;

      await clickButtonByText("Add Environment Variable");
      await sleep(250);

      const inputs = allInputs();
      const emptyKey = inputs.find((el) => !el.value && /key/i.test(el.placeholder || ""));
      const emptyValue = inputs.find((el) => !el.value && /value/i.test(el.placeholder || ""));

      if (!emptyKey || !emptyValue) {
        console.warn(`[ghwv] Could not locate env var row for ${key}`);
        continue;
      }

      emptyKey.value = key;
      fireEvents(emptyKey);
      emptyValue.value = value;
      fireEvents(emptyValue);
      await sleep(200);
    }
  };

  const fillServiceForm = async () => {
    setTextField("Name", preset.name);
    await setSelectLikeField("Language", "Python");
    setTextField("Root Directory", preset.rootDirectory);
    setTextField("Build Command", preset.buildCommand);
    setTextField("Start Command", preset.startCommand);
    await fillEnvVars();
    console.log("[ghwv] Render form autofill completed. Add GHWV_PUBLIC_API_BASE_URL after Render assigns the URL.");
  };

  window.ghwvRenderAutofill = {
    preset,
    fillServiceForm,
    setTextField,
    setSelectLikeField,
    fillEnvVars,
  };

  console.log("[ghwv] Render autofill helper loaded. Run: ghwvRenderAutofill.fillServiceForm()");
})();
