const form = document.querySelector("#translate-form");
const inputText = document.querySelector("#input-text");
const outputText = document.querySelector("#output-text");
const srcLang = document.querySelector("#src-lang");
const tgtLang = document.querySelector("#tgt-lang");
const swapButton = document.querySelector("#swap-button");
const translateButton = document.querySelector("#translate-button");
const copyButton = document.querySelector("#copy-button");
const statusMessage = document.querySelector("#status-message");

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("is-error", isError);
}

function setLoading(isLoading) {
  translateButton.disabled = isLoading;
  translateButton.classList.toggle("is-loading", isLoading);
  translateButton.querySelector(".button-label").textContent = isLoading
    ? "Translating"
    : "Translate";
}

function updateCopyButton() {
  copyButton.disabled = !outputText.value.trim();
}

async function copyTranslation() {
  const translation = outputText.value.trim();
  if (!translation) {
    setStatus("No translation to copy.", true);
    return;
  }

  try {
    await navigator.clipboard.writeText(translation);
  } catch {
    outputText.select();
    document.execCommand("copy");
    outputText.setSelectionRange(0, 0);
  }

  setStatus("Translation copied.");
}

async function translate() {
  const text = inputText.value.trim();
  if (!text) {
    outputText.value = "";
    updateCopyButton();
    setStatus("Enter text to translate.", true);
    inputText.focus();
    return;
  }

  setLoading(true);
  setStatus("Sending request to translation backend...");

  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        srcLang: srcLang.value,
        tgtLang: tgtLang.value,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Translation failed.");
    }

    outputText.value = result.translation;
    updateCopyButton();
    setStatus("Translation complete.");
  } catch (error) {
    outputText.value = "";
    updateCopyButton();
    setStatus(error.message, true);
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  translate();
});

swapButton.addEventListener("click", () => {
  const previousSrcLang = srcLang.value;
  srcLang.value = tgtLang.value;
  tgtLang.value = previousSrcLang;

  const previousInput = inputText.value;
  inputText.value = outputText.value;
  outputText.value = previousInput;
  updateCopyButton();
  setStatus("");
});

copyButton.addEventListener("click", copyTranslation);

updateCopyButton();
