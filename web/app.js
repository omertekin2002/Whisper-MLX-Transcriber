const state = {
  file: null,
  jobId: null,
  pollTimer: null,
  transcript: "",
};

const els = {
  form: document.querySelector("#transcribeForm"),
  dropZone: document.querySelector("#dropZone"),
  fileInput: document.querySelector("#fileInput"),
  dropTitle: document.querySelector("#dropTitle"),
  fileMeta: document.querySelector("#fileMeta"),
  modelSelect: document.querySelector("#modelSelect"),
  languageSelect: document.querySelector("#languageSelect"),
  hfTokenInput: document.querySelector("#hfTokenInput"),
  startButton: document.querySelector("#startButton"),
  statusText: document.querySelector("#statusText"),
  progressText: document.querySelector("#progressText"),
  progressBar: document.querySelector("#progressBar"),
  transcriptTitle: document.querySelector("#transcriptTitle"),
  transcriptText: document.querySelector("#transcriptText"),
  copyButton: document.querySelector("#copyButton"),
  downloadButton: document.querySelector("#downloadButton"),
};

init();

async function init() {
  bindEvents();
  await loadConfig();
}

function bindEvents() {
  els.fileInput.addEventListener("change", () => {
    setFile(els.fileInput.files[0] || null);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    els.dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      els.dropZone.classList.add("is-dragging");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    els.dropZone.addEventListener(eventName, () => {
      els.dropZone.classList.remove("is-dragging");
    });
  });

  els.dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    setFile(event.dataTransfer.files[0] || null);
  });

  els.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await startTranscription();
  });

  els.copyButton.addEventListener("click", async () => {
    await navigator.clipboard.writeText(state.transcript);
    setStatus("Copied", currentProgress());
  });

  els.downloadButton.addEventListener("click", () => {
    if (state.jobId) {
      window.location.href = `/api/jobs/${state.jobId}/transcript`;
    }
  });
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();

  els.modelSelect.innerHTML = "";
  config.models.forEach((model) => {
    const option = document.createElement("option");
    option.value = model.name;
    option.textContent = model.available ? model.name : `${model.name} - download on first use`;
    option.selected = model.name === config.defaultModel;
    els.modelSelect.append(option);
  });

  els.languageSelect.innerHTML = "";
  config.languages.forEach((language) => {
    const option = document.createElement("option");
    option.value = language.code;
    option.textContent = language.label;
    els.languageSelect.append(option);
  });
}

function setFile(file) {
  state.file = file;
  els.startButton.disabled = !file;

  if (!file) {
    els.dropTitle.textContent = "Drop audio here";
    els.fileMeta.textContent = "or choose a file";
    return;
  }

  els.dropTitle.textContent = file.name;
  els.fileMeta.textContent = formatBytes(file.size);
  els.transcriptTitle.textContent = "Ready";
}

async function startTranscription() {
  if (!state.file) {
    return;
  }

  resetTranscript();
  setBusy(true);
  setStatus("Uploading", 1);

  const body = new FormData();
  body.append("file", state.file);
  body.append("model", els.modelSelect.value);
  body.append("language", els.languageSelect.value);
  body.append("hf_token", els.hfTokenInput.value.trim());

  try {
    const response = await fetch("/api/transcriptions", {
      method: "POST",
      body,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed");
    }

    const payload = await response.json();
    state.jobId = payload.jobId;
    pollJob();
    state.pollTimer = window.setInterval(pollJob, 900);
  } catch (error) {
    showFailure(error.message);
  }
}

async function pollJob() {
  if (!state.jobId) {
    return;
  }

  try {
    const response = await fetch(`/api/jobs/${state.jobId}`);
    if (!response.ok) {
      throw new Error("Job disappeared");
    }

    const job = await response.json();
    setStatus(job.stage, job.progress);
    els.transcriptTitle.textContent = `${job.filename} - ${job.status}`;

    if (job.status === "completed") {
      clearPoll();
      state.transcript = job.transcript || "";
      els.transcriptText.value = state.transcript;
      els.transcriptTitle.textContent = `${job.filename} - complete`;
      setBusy(false);
      setResultButtons(Boolean(state.transcript));
    }

    if (job.status === "failed") {
      clearPoll();
      showFailure(job.error || "Transcription failed");
    }
  } catch (error) {
    clearPoll();
    showFailure(error.message);
  }
}

function resetTranscript() {
  state.transcript = "";
  els.transcriptText.value = "";
  els.transcriptTitle.textContent = "Working";
  setResultButtons(false);
}

function setBusy(isBusy) {
  els.startButton.disabled = isBusy || !state.file;
  els.modelSelect.disabled = isBusy;
  els.languageSelect.disabled = isBusy;
  els.hfTokenInput.disabled = isBusy;
  els.fileInput.disabled = isBusy;
}

function setResultButtons(enabled) {
  els.copyButton.disabled = !enabled;
  els.downloadButton.disabled = !enabled;
}

function setStatus(text, progress) {
  els.statusText.textContent = text;
  els.statusText.classList.remove("is-error");
  els.progressText.textContent = `${progress}%`;
  els.progressBar.style.width = `${progress}%`;
}

function showFailure(message) {
  setBusy(false);
  setStatus("Failed", 100);
  els.statusText.classList.add("is-error");
  els.transcriptTitle.textContent = "Error";
  els.transcriptText.value = message;
}

function clearPoll() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function currentProgress() {
  return Number.parseInt(els.progressText.textContent, 10) || 0;
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}
